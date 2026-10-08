#!/usr/bin/env python3
"""
account_change_diff.py: Account Change Intelligence. Compares two account_state
snapshots (contract: account_state v1.0) and reports material changes.

USAGE: python account_change_diff.py previous.json current.json [--pct 10] [--prob 0.10] [--out changes.json]

Detects:
  metrics      numeric changes of at least --pct percent (or a sign flip)
  swot         items added, removed, or whose confidence changed (matched by item id)
  risks        risk-dimension level changes (low < medium < high < critical)
  predictions  probability moved by at least --prob, or the confidence label changed
  stakeholders added, departed, role or strength changed
  opportunities new, removed, stage or value changed
Each change carries a materiality flag, so the skill can explain why it matters
and whether the strategy should change.
"""
import argparse, json

ap = argparse.ArgumentParser()
ap.add_argument("prev")
ap.add_argument("curr")
ap.add_argument("--pct", type=float, default=10)
ap.add_argument("--prob", type=float, default=0.10)
ap.add_argument("--out")
a = ap.parse_args()
P, C = json.load(open(a.prev)), json.load(open(a.curr))
LEV = {"low": 1, "medium": 2, "high": 3, "critical": 4}
ch = {"as_of": {"previous": P.get("as_of"), "current": C.get("as_of")}, "metrics": [], "swot": [], "risks": [],
      "predictions": [], "stakeholders": [], "opportunities": []}

for k in set(P.get("metrics", {})) | set(C.get("metrics", {})):
    p, c = P.get("metrics", {}).get(k), C.get("metrics", {}).get(k)
    if p is None or c is None:
        ch["metrics"].append({"metric": k, "previous": p, "current": c, "change": "added" if p is None else "removed"})
        continue
    if p == 0:
        if c != 0:
            ch["metrics"].append({"metric": k, "previous": p, "current": c, "pct": None, "material": True})
        continue
    pct = (c - p) / abs(p) * 100
    if abs(pct) >= a.pct or (p > 0) != (c > 0):
        ch["metrics"].append({"metric": k, "previous": p, "current": c, "pct": round(pct, 1), "material": abs(pct) >= 2 * a.pct})

def idx(lst, key="id"):
    return {x[key]: x for x in lst or []}

for q in ["strengths", "weaknesses", "opportunities", "threats"]:
    ps, cs = idx(P.get("swot", {}).get(q)), idx(C.get("swot", {}).get(q))
    for i in cs.keys() - ps.keys():
        ch["swot"].append({"quadrant": q, "id": i, "change": "added", "item": cs[i].get("statement")})
    for i in ps.keys() - cs.keys():
        ch["swot"].append({"quadrant": q, "id": i, "change": "removed", "item": ps[i].get("statement")})
    for i in ps.keys() & cs.keys():
        if ps[i].get("confidence") != cs[i].get("confidence"):
            ch["swot"].append({"quadrant": q, "id": i, "change": "confidence", "from": ps[i].get("confidence"), "to": cs[i].get("confidence")})

for dim in set(P.get("risks", {})) | set(C.get("risks", {})):
    p = (P.get("risks", {}).get(dim) or {}).get("level")
    c = (C.get("risks", {}).get(dim) or {}).get("level")
    if p != c:
        d = LEV.get(c, 0) - LEV.get(p, 0)
        ch["risks"].append({"dimension": dim, "from": p, "to": c, "direction": "increased" if d > 0 else "decreased",
                            "material": abs(d) >= 1 and LEV.get(c, 0) >= 3})

pp, cp = idx(P.get("predictions"), "name"), idx(C.get("predictions"), "name")
for n in pp.keys() | cp.keys():
    p, c = pp.get(n), cp.get(n)
    if not p or not c:
        ch["predictions"].append({"prediction": n, "change": "added" if not p else "removed"})
        continue
    dp = (c.get("probability") or 0) - (p.get("probability") or 0)
    if abs(dp) >= a.prob or p.get("confidence") != c.get("confidence"):
        ch["predictions"].append({"prediction": n, "from": p.get("probability"), "to": c.get("probability"),
                                  "delta": round(dp, 3), "confidence": [p.get("confidence"), c.get("confidence")],
                                  "material": abs(dp) >= 2 * a.prob})

ps, cs = idx(P.get("stakeholders"), "name"), idx(C.get("stakeholders"), "name")
for n in cs.keys() - ps.keys():
    ch["stakeholders"].append({"name": n, "change": "new", "role": cs[n].get("role")})
for n in ps.keys() - cs.keys():
    ch["stakeholders"].append({"name": n, "change": "departed_or_missing", "role": ps[n].get("role"),
                               "material": ps[n].get("role") in ("economic_buyer", "champion", "executive_sponsor")})
for n in ps.keys() & cs.keys():
    for f in ["role", "strength", "stance"]:
        if ps[n].get(f) != cs[n].get(f):
            ch["stakeholders"].append({"name": n, "change": f, "from": ps[n].get(f), "to": cs[n].get(f)})

po, co = idx(P.get("opportunities")), idx(C.get("opportunities"))
for i in co.keys() - po.keys():
    ch["opportunities"].append({"id": i, "change": "new", "value": co[i].get("value")})
for i in po.keys() - co.keys():
    ch["opportunities"].append({"id": i, "change": "closed_or_removed"})
for i in po.keys() & co.keys():
    for f in ["stage", "value", "close_date"]:
        if po[i].get(f) != co[i].get(f):
            ch["opportunities"].append({"id": i, "change": f, "from": po[i].get(f), "to": co[i].get(f)})

ch["material_change_count"] = sum(1 for k in ["metrics", "risks", "predictions", "stakeholders"] for x in ch[k] if x.get("material"))
ch["strategy_review_suggested"] = ch["material_change_count"] >= 2 or any(
    x.get("material") for x in ch["stakeholders"]) or any(x.get("to") == "critical" for x in ch["risks"])
print(json.dumps(ch, indent=2))
if a.out:
    json.dump(ch, open(a.out, "w"), indent=2)
