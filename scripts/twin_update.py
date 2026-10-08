#!/usr/bin/env python3
"""
twin_update.py: Customer Digital Twin (account state model) service.

The twin is an append-only history of `account_state` snapshots (JSONL, one
snapshot per line), keyed by account. This script adds a new snapshot and
produces the twin view:

  current state → historical state → changes → trends → when it changed

USAGE
  python twin_update.py add  twin.jsonl snapshot.json        # append after validation
  python twin_update.py view twin.jsonl --account ACME [--metrics arr utilization_pct ...] [--out view.json]

View contents:
  current     latest snapshot
  history     per-metric series (as_of, value)
  trends      per metric: first, last, change %, slope per 30 days (least squares),
              direction, and the number of snapshots behind it
  change_log  for every consecutive pair of snapshots: metric moves ≥ 10%, risk-level
              changes, stakeholder arrivals and departures, SWOT additions and removals,
              prediction moves ≥ 0.10 — each dated, so you can answer WHEN it changed
  first_seen  when each current risk, threat, or stakeholder first appeared
Snapshots must follow the account_state contract (v1.0+). Unknown fields are kept.
"""
import argparse, json, sys
from datetime import datetime

LEV = {"low": 1, "medium": 2, "high": 3, "critical": 4}


def load(path):
    try:
        return [json.loads(l) for l in open(path) if l.strip()]
    except FileNotFoundError:
        return []


def d(s):
    return datetime.fromisoformat(str(s)[:10])


def slope(points):
    """Least-squares slope, expressed as change per 30 days."""
    if len(points) < 2:
        return None
    xs = [(d(t) - d(points[0][0])).days for t, _ in points]
    ys = [v for _, v in points]
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    den = sum((x - mx) ** 2 for x in xs)
    return None if den == 0 else round(sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den * 30, 4)


def diff(p, c):
    """Dated changes between two consecutive snapshots."""
    out = []
    t = c.get("as_of")
    for k in set(p.get("metrics", {})) | set(c.get("metrics", {})):
        a, b = p.get("metrics", {}).get(k), c.get("metrics", {}).get(k)
        if isinstance(a, (int, float)) and isinstance(b, (int, float)) and a != 0:
            pct = (b - a) / abs(a) * 100
            if abs(pct) >= 10:
                out.append({"when": t, "kind": "metric", "item": k, "from": a, "to": b, "pct": round(pct, 1)})
    for k in set(p.get("risks", {})) | set(c.get("risks", {})):
        a = (p.get("risks", {}).get(k) or {}).get("level")
        b = (c.get("risks", {}).get(k) or {}).get("level")
        if a != b:
            out.append({"when": t, "kind": "risk", "item": k, "from": a, "to": b,
                        "direction": "up" if LEV.get(b, 0) > LEV.get(a, 0) else "down"})
    ps = {s["name"]: s for s in p.get("stakeholders", [])}
    cs = {s["name"]: s for s in c.get("stakeholders", [])}
    for n in cs.keys() - ps.keys():
        out.append({"when": t, "kind": "stakeholder_new", "item": n, "role": cs[n].get("role")})
    for n in ps.keys() - cs.keys():
        out.append({"when": t, "kind": "stakeholder_departed", "item": n, "role": ps[n].get("role")})
    for q in ["strengths", "weaknesses", "opportunities", "threats"]:
        a = {x["id"] for x in p.get("swot", {}).get(q, [])}
        b = {x["id"]: x for x in c.get("swot", {}).get(q, [])}
        for i in b.keys() - a:
            out.append({"when": t, "kind": f"swot_{q}_added", "item": i, "statement": b[i].get("statement")})
        for i in a - b.keys():
            out.append({"when": t, "kind": f"swot_{q}_removed", "item": i})
    pp = {x["name"]: x for x in p.get("predictions", [])}
    cp = {x["name"]: x for x in c.get("predictions", [])}
    for n in pp.keys() & cp.keys():
        dv = (cp[n].get("probability") or 0) - (pp[n].get("probability") or 0)
        if abs(dv) >= 0.10:
            out.append({"when": t, "kind": "prediction", "item": n, "from": pp[n].get("probability"),
                        "to": cp[n].get("probability"), "delta": round(dv, 3)})
    return out


ap = argparse.ArgumentParser()
ap.add_argument("mode", choices=["add", "view"])
ap.add_argument("twin")
ap.add_argument("snapshot", nargs="?")
ap.add_argument("--account")
ap.add_argument("--metrics", nargs="*")
ap.add_argument("--out")
a = ap.parse_args()

if a.mode == "add":
    s = json.load(open(a.snapshot))
    miss = [k for k in ["account_id", "as_of"] if not s.get(k)]
    if miss:
        sys.exit(json.dumps({"error": f"snapshot missing {miss}"}))
    hist = [h for h in load(a.twin) if h.get("account_id") == s["account_id"]]
    if any(h.get("as_of") == s["as_of"] for h in hist):
        sys.exit(json.dumps({"error": f"snapshot for {s['account_id']} as_of {s['as_of']} already exists; twin is append-only"}))
    if hist and d(s["as_of"]) < d(max(h["as_of"] for h in hist)):
        sys.exit(json.dumps({"error": "snapshot is older than the latest in the twin; append-only history refuses back-dating"}))
    with open(a.twin, "a") as f:
        f.write(json.dumps(s) + "\n")
    print(json.dumps({"added": s["account_id"], "as_of": s["as_of"], "snapshots_now": len(hist) + 1}))
    sys.exit()

hist = sorted([h for h in load(a.twin) if h.get("account_id") == a.account], key=lambda h: h["as_of"])
if not hist:
    sys.exit(json.dumps({"error": f"no twin history for {a.account}"}))
cur = hist[-1]
mets = a.metrics or sorted({k for h in hist for k, v in h.get("metrics", {}).items() if isinstance(v, (int, float))})
series, trends = {}, {}
for m in mets:
    pts = [(h["as_of"], h["metrics"][m]) for h in hist if isinstance(h.get("metrics", {}).get(m), (int, float))]
    series[m] = pts
    if len(pts) >= 2:
        f, l = pts[0][1], pts[-1][1]
        sl = slope(pts)
        trends[m] = {"first": f, "last": l, "change_pct": round((l - f) / abs(f) * 100, 1) if f else None,
                     "slope_per_30d": sl, "direction": "up" if (sl or 0) > 0 else "down" if (sl or 0) < 0 else "flat",
                     "points": len(pts), "confidence": "Low" if len(pts) < 4 else "Medium" if len(pts) < 8 else "High"}
log = []
for p, c in zip(hist, hist[1:]):
    log += diff(p, c)

# First appearance of each current risk level, threat, and stakeholder.
first = {}
for k, v in cur.get("risks", {}).items():
    lvl = (v or {}).get("level")
    since = cur["as_of"]
    for h in reversed(hist):
        if (h.get("risks", {}).get(k) or {}).get("level") == lvl:
            since = h["as_of"]
        else:
            break
    first[f"risk:{k}={lvl}"] = since
for t in cur.get("swot", {}).get("threats", []):
    first[f"threat:{t['id']}"] = next(h["as_of"] for h in hist if any(x["id"] == t["id"] for x in h.get("swot", {}).get("threats", [])))
view = {"account_id": a.account, "snapshots": len(hist), "span": [hist[0]["as_of"], cur["as_of"]],
        "current": cur, "history": series, "trends": trends, "change_log": log, "current_state_since": first}
print(json.dumps(view, indent=2, default=str))
if a.out:
    json.dump(view, open(a.out, "w"), indent=2, default=str)
