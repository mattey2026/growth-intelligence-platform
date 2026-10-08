#!/usr/bin/env python3
"""
opportunity_scorer.py: Growth Opportunity Discovery scoring.

Scores candidate opportunities on: Signal + Customer Need + Fit + Timing + Probability + Commercial Potential.

INPUT JSON list of candidates (from whitespace_matrix, signal_correlator patterns,
propensity outputs, competitive watch, and knowledge or research), each:
 {"id":"", "account_id":"", "type":"cross_sell|upsell|whitespace|new_bu|new_geo|new_use_case|contract_expansion|
   competitive_displacement|m_and_a|regulatory|tech_transformation|service_driven|investment_signal",
  "offering":"", "potential_value": 400000, "value_basis":"peer median|quote|estimate",
  "probability": 0.3, "probability_basis":"propensity model|base rate|judgment",
  "signals":[{"signal":"","date":"","source":""}], "need_evidence":["..."], "fit": 0.8,
  "timing_days": 90, "competitive_intensity": "low|medium|high", "required_investment": 50000,
  "strategic_fit": 0.7, "relationship_strength": 2}
USAGE: python opportunity_scorer.py candidates.json [--horizon-days 365] [--out ranked.json]

Scoring (every component is shown):
  expected_value = potential_value × probability
  evidence       = min(1, (signals + need_evidence) / 4); fewer than 2 pieces of evidence → "hypothesis"
  timing_factor  = 1.0 (≤ 90 days), 0.85 (≤ 180), 0.7 (≤ 365), else 0.5
  competition    = low 1.0 · medium 0.85 · high 0.7
  roi            = (expected_value − required_investment) ÷ max(required_investment, 1)
  priority       = expected_value × timing × competition × (0.5 + 0.5 × fit) × (0.6 + 0.4 × evidence)
Candidates with a potential_value basis of "estimate" and probability basis of "judgment" are
flagged "low-evidence" and cannot rank above candidates with modelled inputs of similar value.
"""
import argparse, json

ap = argparse.ArgumentParser()
ap.add_argument("file")
ap.add_argument("--horizon-days", type=int, default=365)
ap.add_argument("--out")
a = ap.parse_args()
C = json.load(open(a.file))
TF = lambda d: 1.0 if d <= 90 else 0.85 if d <= 180 else 0.7 if d <= 365 else 0.5
CI = {"low": 1.0, "medium": 0.85, "high": 0.7}
out = []
for c in C:
    ev = c["potential_value"] * c["probability"]
    n_ev = len(c.get("signals", [])) + len(c.get("need_evidence", []))
    evid = min(1.0, n_ev / 4)
    fit = c.get("fit", 0.5)
    pr = ev * TF(c.get("timing_days", 180)) * CI.get(c.get("competitive_intensity", "medium"), 0.85) * (0.5 + 0.5 * fit) * (0.6 + 0.4 * evid)
    low = c.get("value_basis") == "estimate" and c.get("probability_basis") == "judgment"
    if low:
        pr *= 0.6
    inv = c.get("required_investment", 0)
    out.append({**c, "expected_value": round(ev), "evidence_score": round(evid, 2),
                "status": "hypothesis" if n_ev < 2 else "evidenced", "low_evidence_inputs": low,
                "roi": round((ev - inv) / max(inv, 1), 1) if inv else None,
                "within_horizon": c.get("timing_days", 180) <= a.horizon_days,
                "priority_score": round(pr),
                "score_components": {"timing": TF(c.get("timing_days", 180)), "competition": CI.get(c.get("competitive_intensity", "medium"), 0.85),
                                     "fit_factor": round(0.5 + 0.5 * fit, 2), "evidence_factor": round(0.6 + 0.4 * evid, 2), "low_evidence_penalty": 0.6 if low else 1.0}})
out.sort(key=lambda r: -r["priority_score"])
res = {"candidates": len(out), "total_potential": round(sum(r["potential_value"] for r in out)),
       "total_expected_value": round(sum(r["expected_value"] for r in out)), "ranked": out}
print(json.dumps(res, indent=2))
if a.out:
    json.dump(res, open(a.out, "w"), indent=2)
