#!/usr/bin/env python3
"""
signal_ranker.py: ranks proactive signals for the Daily Growth Briefing.

INPUT JSON: {"user": {"role": "account_executive|manager|executive|csm|revops",
                      "owned_accounts": [...], "owned_opportunities": [...]},
             "signals": [{"id":"", "type":"deal_risk|account_change|opportunity|health|pipeline_anomaly|
                          forecast_change|stakeholder_change|competitive|renewal|revenue_risk|service|finance",
                          "entity_type":"opportunity|account|pipeline|forecast", "entity_id":"",
                          "headline":"", "why_it_matters":"", "value_at_stake":0, "days_to_impact":30,
                          "confidence":"High|Medium|Low", "novelty":"new|changed|repeat",
                          "source_skill":"", "evidence":[], "recommended_action":"",
                          "claude_can_do":"", "approval_required":true}]}
USAGE: python signal_ranker.py signals.json [--max 7] [--out briefing.json]

Score = value_weight × urgency × confidence × novelty × relevance
  value_weight = sqrt(value_at_stake / max value_at_stake in the set)  (relative; keeps large gaps visible)
  urgency      = 1.5 if ≤ 7 days, 1.2 if ≤ 30, 1.0 if ≤ 90, else 0.7
  confidence   = High 1.0 · Medium 0.75 · Low 0.5
  novelty      = new 1.0 · changed 0.9 · repeat 0.4  (the user already saw it)
  relevance    = 1.3 if the entity is owned by the user · 1.0 otherwise;
                 per-role type weights (below)
Keeps the highest-scoring signal per entity, returns the top --max, and groups
the rest as "also changed". Every item keeps its evidence and source skill.
"""
import argparse, json, math

ROLE = {"account_executive": {"deal_risk": 1.3, "opportunity": 1.2, "stakeholder_change": 1.2, "competitive": 1.1,
                              "pipeline_anomaly": 0.6, "forecast_change": 0.7},
        "manager": {"deal_risk": 1.2, "forecast_change": 1.3, "pipeline_anomaly": 1.3},
        "executive": {"forecast_change": 1.4, "revenue_risk": 1.4, "pipeline_anomaly": 1.2, "renewal": 1.2},
        "csm": {"health": 1.4, "renewal": 1.3, "service": 1.3, "opportunity": 1.1},
        "revops": {"pipeline_anomaly": 1.4, "forecast_change": 1.3}}
CONF = {"High": 1.0, "Medium": 0.75, "Low": 0.5}
NOV = {"new": 1.0, "changed": 0.9, "repeat": 0.4}

ap = argparse.ArgumentParser()
ap.add_argument("file")
ap.add_argument("--max", type=int, default=7)
ap.add_argument("--out")
a = ap.parse_args()
d = json.load(open(a.file))
u = d.get("user", {})
owned = set(u.get("owned_accounts", [])) | set(u.get("owned_opportunities", []))
rw = ROLE.get(u.get("role"), {})
vmax = max([s.get("value_at_stake", 0) for s in d["signals"]] + [1])
scored = []
for s in d["signals"]:
    days = s.get("days_to_impact", 60)
    urg = 1.5 if days <= 7 else 1.2 if days <= 30 else 1.0 if days <= 90 else 0.7
    rel = (1.3 if s.get("entity_id") in owned else 1.0) * rw.get(s.get("type"), 1.0)
    sc = (math.sqrt(max(s.get("value_at_stake", 0), 0) / vmax) * urg * CONF.get(s.get("confidence"), 0.5)
          * NOV.get(s.get("novelty"), 0.9) * rel)
    scored.append({**s, "score": round(sc, 3),
                   "score_parts": {"urgency": urg, "relevance": round(rel, 2),
                                   "confidence": CONF.get(s.get("confidence"), 0.5),
                                   "novelty": NOV.get(s.get("novelty"), 0.9)}})
scored.sort(key=lambda x: -x["score"])
seen, top, rest = set(), [], []
for s in scored:
    k = (s.get("entity_type"), s.get("entity_id"))
    if k in seen or len(top) >= a.max:
        rest.append({"id": s["id"], "headline": s.get("headline"), "score": s["score"]})
        continue
    seen.add(k)
    top.append(s)
out = {"user_role": u.get("role"), "top": top, "also_changed": rest,
       "value_at_stake_in_top": sum(s.get("value_at_stake", 0) for s in top)}
print(json.dumps(out, indent=2))
if a.out:
    json.dump(out, open(a.out, "w"), indent=2)
