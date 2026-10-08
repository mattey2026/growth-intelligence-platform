#!/usr/bin/env python3
"""
signal_correlator.py: Growth Signal Orchestrator correlation service.

Correlates normalized signals across functions into business PATTERNS (risks
and opportunities). This is not an alert engine: each detected pattern returns
  - which conditions matched (with dated evidence and source function)
  - the temporal sequence (what happened first)
  - corroboration (how many independent functions agree)
  - what is still unconfirmed (conditions to check next)
  - confidence, the skills and predictions to trigger, and candidate actions

INPUT signals (JSON list or JSONL). One signal:
  {"entity_id":"ACME","signal":"product_usage","direction":"down|up|event",
   "magnitude":-0.18,"date":"2026-09-20","function":"product|marketing|sales|cs|service|finance|partner|external",
   "source":"usage warehouse","evidence":"Active users 820→672 (−18%) 90d"}
Signal names follow references/signal-vocabulary.md.

USAGE: python signal_correlator.py signals.json [--patterns custom_patterns.json] [--window 120] [--asof 2026-09-28] [--out patterns.json]
"""
import argparse, json
from collections import defaultdict
from datetime import datetime, timedelta

DEFAULT_PATTERNS = [
 {"id": "compound_customer_risk", "kind": "risk", "title": "Compounding customer risk across functions",
  "conditions": [
   {"signal": "marketing_engagement", "direction": "down", "weight": 1},
   {"signal": "product_usage", "direction": "down", "weight": 2},
   {"signal": "service_incidents", "direction": "up", "weight": 2},
   {"signal": "executive_sponsor_departed", "direction": "event", "weight": 3},
   {"signal": "payment_disputes", "direction": "up", "weight": 2},
   {"signal": "dso", "direction": "up", "weight": 1}],
  "min_matched": 3, "min_functions": 2,
  "significance": "Several independent functions show the relationship weakening; renewal and expansion are both at risk.",
  "trigger_skills": ["customer-digital-twin", "renewal-expansion-radar", "relationship-intelligence", "account-intelligence-swot-planning"],
  "trigger_predictions": ["churn", "revenue_at_risk"],
  "candidate_actions": ["Executive re-engagement plan", "Service recovery plan with the service owner", "Finance: dispute resolution", "Account strategy review: protect before expand"]},
 {"id": "expansion_readiness", "kind": "opportunity", "title": "Expansion readiness",
  "conditions": [
   {"signal": "marketing_engagement", "direction": "up", "weight": 1},
   {"signal": "new_executive", "direction": "event", "weight": 2},
   {"signal": "product_adoption", "direction": "up", "weight": 2},
   {"signal": "competitor_contract_expiring", "direction": "event", "weight": 3},
   {"signal": "whitespace_identified", "direction": "event", "weight": 2},
   {"signal": "customer_investment", "direction": "event", "weight": 2}],
  "min_matched": 3, "min_functions": 2,
  "significance": "Engagement, adoption, and timing align; there is a window to expand or displace.",
  "trigger_skills": ["growth-opportunity-discovery", "relationship-intelligence", "competitive-intelligence", "account-intelligence-swot-planning"],
  "trigger_predictions": ["expansion", "cross_sell"],
  "candidate_actions": ["Meet the new executive within 30 days", "Build the expansion business case", "Competitive displacement plan before the contract expiry"]},
 {"id": "competitive_displacement_risk", "kind": "risk", "title": "Competitive displacement risk",
  "conditions": [
   {"signal": "competitor_mention", "direction": "up", "weight": 2},
   {"signal": "rfp_issued", "direction": "event", "weight": 3},
   {"signal": "price_benchmark_request", "direction": "event", "weight": 2},
   {"signal": "champion_engagement", "direction": "down", "weight": 2},
   {"signal": "renewal_within_180d", "direction": "event", "weight": 1}],
  "min_matched": 2, "min_functions": 1,
  "significance": "A competitor is being evaluated in scope we own.",
  "trigger_skills": ["competitive-intelligence", "relationship-intelligence", "pricing-intelligence"],
  "trigger_predictions": ["competitive_displacement", "churn"],
  "candidate_actions": ["Competitive response plan", "Value realization review", "Pricing pre-emption analysis"]},
 {"id": "executive_access_loss", "kind": "risk", "title": "Executive access loss",
  "conditions": [
   {"signal": "executive_sponsor_departed", "direction": "event", "weight": 3},
   {"signal": "executive_engagement", "direction": "down", "weight": 2},
   {"signal": "single_threaded", "direction": "event", "weight": 2},
   {"signal": "unanswered_commitment", "direction": "event", "weight": 1}],
  "min_matched": 2, "min_functions": 1,
  "significance": "Access to power is weakening; deals and renewal depend on too few people.",
  "trigger_skills": ["relationship-intelligence"], "trigger_predictions": ["stakeholder_attrition"],
  "candidate_actions": ["Executive sponsor program", "Multi-threading plan", "Close open commitments"]},
 {"id": "service_driven_commercial_opportunity", "kind": "opportunity", "title": "Service-driven commercial opportunity",
  "conditions": [
   {"signal": "service_incidents", "direction": "up", "weight": 2},
   {"signal": "recurring_issue_category", "direction": "event", "weight": 2},
   {"signal": "offering_addresses_issue", "direction": "event", "weight": 3},
   {"signal": "budget_available", "direction": "event", "weight": 1}],
  "min_matched": 3, "min_functions": 2,
  "significance": "A recurring service problem matches an offering that solves it. Fix first; commercial follows.",
  "trigger_skills": ["growth-opportunity-discovery", "renewal-expansion-radar"], "trigger_predictions": ["cross_sell"],
  "candidate_actions": ["Service recovery first", "Then propose the managed or premium offering with a quantified business case"]},
 {"id": "margin_erosion", "kind": "risk", "title": "Account margin erosion",
  "conditions": [
   {"signal": "discount_depth", "direction": "up", "weight": 2},
   {"signal": "cost_to_serve", "direction": "up", "weight": 2},
   {"signal": "gross_margin", "direction": "down", "weight": 3},
   {"signal": "free_services", "direction": "event", "weight": 1}],
  "min_matched": 2, "min_functions": 2,
  "significance": "Revenue is holding but the account economics are deteriorating.",
  "trigger_skills": ["pricing-intelligence"], "trigger_predictions": ["margin_at_risk"],
  "candidate_actions": ["Account economics review", "Renewal repricing strategy", "Cost-to-serve reduction"]},
]


def d(s):
    return datetime.fromisoformat(str(s)[:10])


ap = argparse.ArgumentParser()
ap.add_argument("signals")
ap.add_argument("--patterns")
ap.add_argument("--window", type=int, default=120)
ap.add_argument("--asof")
ap.add_argument("--out")
a = ap.parse_args()
raw = open(a.signals).read().strip()
sig = json.loads(raw) if raw.startswith("[") else [json.loads(l) for l in raw.splitlines() if l.strip()]
pats = DEFAULT_PATTERNS + (json.load(open(a.patterns)) if a.patterns else [])
asof = d(a.asof) if a.asof else max(d(s["date"]) for s in sig)
cut = asof - timedelta(days=a.window)
by = defaultdict(list)
for s in sig:
    if d(s["date"]) >= cut:
        by[s["entity_id"]].append(s)

found = []
for ent, ss in by.items():
    for p in pats:
        matched, missing = [], []
        for c in p["conditions"]:
            hits = [s for s in ss if s["signal"] == c["signal"] and s.get("direction") == c["direction"]]
            (matched if hits else missing).append((c, sorted(hits, key=lambda s: s["date"])))
        funcs = {h["function"] for _, hs in matched for h in hs}
        if len(matched) < p["min_matched"] or len(funcs) < p.get("min_functions", 1):
            continue
        tw = sum(c["weight"] for c in p["conditions"])
        mw = sum(c["weight"] for c, _ in matched)
        strength = round(mw / tw, 2)
        seq = sorted([h for _, hs in matched for h in hs], key=lambda s: s["date"])
        conf = ("High" if len(funcs) >= 3 and strength >= 0.6 else
                "Medium" if len(funcs) >= 2 and strength >= 0.4 else "Low")
        found.append({"entity_id": ent, "pattern": p["id"], "kind": p["kind"], "title": p["title"],
                      "strength": strength, "confidence": conf,
                      "independent_functions": sorted(funcs),
                      "sequence": [{"date": h["date"], "function": h["function"], "signal": h["signal"],
                                    "direction": h["direction"], "evidence": h.get("evidence"), "source": h.get("source")} for h in seq],
                      "unconfirmed": [c["signal"] + " " + c["direction"] for c, _ in missing],
                      "significance": p["significance"], "trigger_skills": p["trigger_skills"],
                      "trigger_predictions": p["trigger_predictions"], "candidate_actions": p["candidate_actions"],
                      "first_signal": seq[0]["date"], "latest_signal": seq[-1]["date"]})
found.sort(key=lambda f: (-{"High": 3, "Medium": 2, "Low": 1}[f["confidence"]], -f["strength"]))
res = {"as_of": str(asof.date()), "window_days": a.window, "entities_scanned": len(by),
       "signals_in_window": sum(len(v) for v in by.values()), "patterns": found,
       "note": "Patterns are correlations of signals, not proof of cause. The orchestrator must explain them in context and confirm the 'unconfirmed' items before action."}
print(json.dumps(res, indent=2))
if a.out:
    json.dump(res, open(a.out, "w"), indent=2)
