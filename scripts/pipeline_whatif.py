#!/usr/bin/env python3
"""
pipeline_whatif.py: pipeline intelligence plus deal-level what-if scenarios.

INPUT: canonical opportunities CSV (from normalize.py or a CRM export). Columns:
  opportunity_id, account_id, owner_id, amount, close_date, outcome (open/won/lost)
  optional: probability (from deal-risk-intelligence), stage_index, created_date, segment
CONFIG JSON (--config):
{
 "period_start": "2026-10-01", "period_end": "2026-12-31", "target": 5000000,
 "closed_to_date": 1200000, "correlation": 0.2,
 "stage_rates": {"1":0.05,"2":0.12,"3":0.25,"4":0.45,"5":0.65},   # used when probability is missing
 "new_pipeline": {"expected_amount": 800000, "conversion": 0.15},   # pipeline created and closed in-period
 "scenarios": {
   "deal_A_slips":   {"slip": ["O12"]},
   "deal_B_lost":    {"lose": ["O7"]},
   "win_prob_down":  {"prob_multiplier": 0.85},
   "creation_slows": {"new_pipeline_multiplier": 0.6},
   "rep_unavailable":{"rep_unavailable": "R3", "reassign_retention": 0.5},
   "big_expansion":  {"add": [{"opportunity_id":"X1","amount":900000,"probability":0.4}]}
 }
}
USAGE: python pipeline_whatif.py opps.csv --config cfg.json [--out result.json]

Descriptive: coverage, weighted pipeline, aging vs the median age of won deals,
concentration (top-5 share, HHI), per-rep exposure, and stage mix.
Predictive: correlated Monte Carlo bookings range P10/P50/P90 for the base case
and for each scenario, with the delta vs base and the probability of reaching target.
"""
import argparse, json
import numpy as np
import pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument("csv")
ap.add_argument("--config", required=True)
ap.add_argument("--out")
ap.add_argument("--n", type=int, default=20000)
a = ap.parse_args()
cfg = json.load(open(a.config))
df = pd.read_csv(a.csv)
for c in ["close_date", "created_date"]:
    if c in df:
        df[c] = pd.to_datetime(df[c], errors="coerce", format="mixed")
ps, pe = pd.Timestamp(cfg["period_start"]), pd.Timestamp(cfg["period_end"])
target = cfg.get("target")
closed = cfg.get("closed_to_date", 0)
openq = df[(df.outcome == "open") & (df.close_date >= ps) & (df.close_date <= pe)].copy()

# Fill missing probabilities from stage rates, and record the source of each.
sr = {int(k): v for k, v in cfg.get("stage_rates", {}).items()}
if "probability" not in openq:
    openq["probability"] = np.nan
src = np.where(openq["probability"].notna(), "model", "stage_rate")
if "stage_index" in openq:
    openq["probability"] = openq["probability"].fillna(openq["stage_index"].map(sr))
openq["probability"] = openq["probability"].fillna(0.2)
openq["prob_source"] = src

desc = {"open_in_period": int(len(openq)), "open_amount": round(float(openq.amount.sum())),
        "weighted": round(float((openq.amount * openq.probability).sum())),
        "probability_sources": pd.Series(src).value_counts().to_dict()}
if target:
    remaining = max(target - closed, 1)
    desc["coverage_ratio"] = round(float(openq.amount.sum() / remaining), 2)
    desc["weighted_coverage"] = round(float((openq.amount * openq.probability).sum() / remaining), 2)
amt = openq.amount.values
share = np.sort(amt)[::-1] / amt.sum() if amt.sum() else amt
desc["concentration"] = {"top5_share": round(float(share[:5].sum()), 3), "hhi": round(float((share ** 2).sum()), 3)}
if "owner_id" in openq:
    desc["rep_exposure"] = (openq.groupby("owner_id").amount.sum().sort_values(ascending=False)
                            .round().astype(int).head(10).to_dict())
won = df[df.outcome == "won"]
if "created_date" in df and len(won) >= 20 and won["created_date"].notna().any():
    won_age = (won.close_date - won.created_date).dt.days
    med = float(won_age.median())
    openq["age"] = (pd.Timestamp.now() - openq.created_date).dt.days
    desc["aging"] = {"median_won_cycle_days": med,
                     "open_older_than_1.5x_median": int((openq.age > 1.5 * med).sum()),
                     "amount_in_aged_deals": round(float(openq[openq.age > 1.5 * med].amount.sum()))}
    closed_hist = df[df.outcome.isin(["won", "lost"])]
    desc["historical_win_rate"] = round(float((closed_hist.outcome == "won").mean()), 3)
if "stage_index" in openq:
    desc["stage_mix"] = openq.groupby("stage_index").amount.sum().round().astype(int).to_dict()

def simulate(o, newpipe_mult=1.0):
    """Correlated Monte Carlo over deal outcomes, plus in-period new pipeline.
    Every scenario reuses the same seed (common random numbers), so deltas
    reflect the scenario change rather than simulation noise."""
    rng = np.random.default_rng(3)
    p = np.clip(o.probability.values, 1e-4, 1 - 1e-4)
    lg = np.log(p / (1 - p))
    shock = rng.normal(0, cfg.get("correlation", 0.2) * 2, (a.n, 1))
    wins = rng.random((a.n, len(p))) < 1 / (1 + np.exp(-(lg + shock)))
    tot = closed + wins @ o.amount.values
    npc = cfg.get("new_pipeline")
    if npc:
        mean_new = npc["expected_amount"] * newpipe_mult * npc["conversion"]
        tot = tot + rng.gamma(4, mean_new / 4, a.n)  # right-skewed new-business contribution
    r = {k: round(float(np.percentile(tot, q))) for k, q in [("P10", 10), ("P50", 50), ("P90", 90)]}
    r["expected"] = round(float(tot.mean()))
    if target:
        r["prob_reach_target"] = round(float((tot >= target).mean()), 3)
    return r


base = simulate(openq)
scen = {}
for name, s in cfg.get("scenarios", {}).items():
    o = openq.copy()
    notes = []
    for oid in s.get("slip", []):
        n0 = len(o)
        o = o[o.opportunity_id.astype(str) != str(oid)]
        notes.append(f"{oid} slips out of period" if len(o) < n0 else f"{oid} not found in period")
    for oid in s.get("lose", []):
        n0 = len(o)
        o = o[o.opportunity_id.astype(str) != str(oid)]
        notes.append(f"{oid} lost" if len(o) < n0 else f"{oid} not found")
    if "prob_multiplier" in s:
        o["probability"] = (o.probability * s["prob_multiplier"]).clip(0, 1)
        notes.append(f"all probabilities × {s['prob_multiplier']}")
    if "rep_unavailable" in s:
        m = o.owner_id.astype(str) == str(s["rep_unavailable"])
        ret = s.get("reassign_retention", 0.5)
        o.loc[m, "probability"] = o.loc[m, "probability"] * ret
        notes.append(f"rep {s['rep_unavailable']} unavailable: {int(m.sum())} deals, probability × {ret} after reassignment (assumption)")
    for add in s.get("add", []):
        o = pd.concat([o, pd.DataFrame([add])], ignore_index=True)
        notes.append(f"added {add.get('opportunity_id')} {add.get('amount')} at p={add.get('probability')}")
    r = simulate(o, s.get("new_pipeline_multiplier", 1.0))
    if "new_pipeline_multiplier" in s:
        notes.append(f"in-period pipeline creation × {s['new_pipeline_multiplier']}")
    r["delta_P50_vs_base"] = r["P50"] - base["P50"]
    r["changes"] = notes
    scen[name] = r

var = openq.amount ** 2 * openq.probability * (1 - openq.probability)
swing = openq.assign(variance_share=(var / var.sum()).round(3)).sort_values("variance_share", ascending=False)
res = {"descriptive": desc, "base_forecast": base, "scenarios": scen,
       "swing_deals": swing[["opportunity_id", "amount", "probability", "variance_share"]].head(8).to_dict("records"),
       "assumptions": [f"Deal correlation {cfg.get('correlation', 0.2)} (shared quarter shock)",
                       "Missing probabilities filled from stage rates (see probability_sources)",
                       "Rep-unavailable retention is an assumption; replace with historical reassignment outcomes if known"]}
print(json.dumps(res, indent=2, default=str))
if a.out:
    json.dump(res, open(a.out, "w"), indent=2, default=str)
