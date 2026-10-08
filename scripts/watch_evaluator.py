#!/usr/bin/env python3
"""
watch_evaluator.py: Business Watch / Growth Watch condition evaluator.

WATCHES JSON (defined by users, approved by owners):
[{"id":"w1","name":"Strategic account health drop","owner":"vp_sales",
  "entity_type":"account","filter":{"tier":"strategic"},
  "metric":"health_score","condition":"pct_change","operator":"<=","threshold":-20,"window":"since_previous",
  "severity":"high","investigate_with":["customer-digital-twin","growth-signal-orchestrator"]},
 {"id":"w2","name":"Large deal slips","entity_type":"opportunity","filter":{"min_amount":5000000},
  "metric":"close_date","condition":"moved_later","severity":"high","investigate_with":["deal-intelligence"]},
 {"id":"w3","name":"Coverage below target","entity_type":"forecast","metric":"coverage_ratio",
  "condition":"value","operator":"<","threshold":3.0,"severity":"medium","investigate_with":["pipeline-forecast-intelligence"]}]

STATE JSON: {"previous": {"account": {...}, "opportunity": {...}, "forecast": {...}},
             "current":  {"account": {"ACME": {"tier":"strategic","health_score":58, ...}}, ...}}
USAGE: python watch_evaluator.py watches.json state.json [--out fired.json]

Conditions: value (op, threshold) · pct_change (op, threshold) · crossed (crossed a threshold
since previous) · moved_later (dates) · event (field changed to a truthy or new value)
Each fired watch includes the entity, previous → current value, and the skills to
investigate with. Watches with unknown metrics are reported as misconfigured, never
silently skipped.
"""
import argparse, json
import operator as op

OPS = {"<": op.lt, "<=": op.le, ">": op.gt, ">=": op.ge, "==": op.eq}
ap = argparse.ArgumentParser()
ap.add_argument("watches")
ap.add_argument("state")
ap.add_argument("--out")
a = ap.parse_args()
W = json.load(open(a.watches))
S = json.load(open(a.state))
fired, misconf = [], []


def passes(ent, flt):
    for k, v in (flt or {}).items():
        if k == "min_amount":
            if (ent.get("amount") or 0) < v:
                return False
        elif ent.get(k) != v:
            return False
    return True


for w in W:
    cur = S["current"].get(w["entity_type"], {})
    prev = S.get("previous", {}).get(w["entity_type"], {})
    if cur and not any(w["metric"] in e for e in cur.values()):
        misconf.append({"watch": w["id"], "reason": f"metric '{w['metric']}' not present in current {w['entity_type']} state"})
        continue
    for eid, e in cur.items():
        if not passes(e, w.get("filter")):
            continue
        c, p = e.get(w["metric"]), (prev.get(eid) or {}).get(w["metric"])
        hit, detail = False, {}
        cond = w["condition"]
        if cond == "value" and c is not None:
            hit = OPS[w["operator"]](c, w["threshold"])
        elif cond == "pct_change" and isinstance(c, (int, float)) and isinstance(p, (int, float)) and p:
            ch = (c - p) / abs(p) * 100
            hit = OPS[w["operator"]](ch, w["threshold"])
            detail["pct_change"] = round(ch, 1)
        elif cond == "crossed" and c is not None and p is not None:
            t = w["threshold"]
            hit = (p >= t > c) or (p < t <= c)
        elif cond == "moved_later" and c and p:
            hit = str(c)[:10] > str(p)[:10]
        elif cond == "event":
            hit = bool(c) and c != p
        if hit:
            fired.append({"watch": w["id"], "name": w["name"], "severity": w.get("severity", "medium"), "owner": w.get("owner"),
                          "entity_type": w["entity_type"], "entity_id": eid, "metric": w["metric"],
                          "previous": p, "current": c, **detail, "investigate_with": w.get("investigate_with", [])})
fired.sort(key=lambda f: {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(f["severity"], 2))
res = {"watches": len(W), "fired": fired, "misconfigured": misconf,
       "next_step": "For each fired watch: investigate with the listed skills, explain the cause, predict the impact, recommend an action (approval-gated)."}
print(json.dumps(res, indent=2, default=str))
if a.out:
    json.dump(res, open(a.out, "w"), indent=2, default=str)
