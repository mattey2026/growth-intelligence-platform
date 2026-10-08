#!/usr/bin/env python3
"""
forecast_sim.py: Monte Carlo bookings range from deal-level probabilities.

INPUT: a deal_risk JSON (from deal-risk-intelligence) or a CSV with the columns
       opportunity_id, amount, probability[, prob_low, prob_high]
USAGE: python forecast_sim.py deals.csv --closed 2100000 --commit 4200000 --quota 5000000 [--corr 0.2]

Each deal is simulated as won or lost using its probability. --corr adds a shared
"quarter shock" that moves all probabilities together. Real deals are not
independent (market, budget cycles), so a correlation of 0.1-0.3 gives more
honest, wider ranges. Where a deal's probability band is provided, each draw
samples within that band to reflect model uncertainty.
Outputs P10/P50/P90, the probability of reaching commit and quota, and the
deals that account for the most variance.
"""
import argparse, json
import numpy as np
import pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument("file")
ap.add_argument("--closed", type=float, default=0)
ap.add_argument("--commit", type=float)
ap.add_argument("--quota", type=float)
ap.add_argument("--corr", type=float, default=0.2)
ap.add_argument("--n", type=int, default=20000)
ap.add_argument("--seed", type=int, default=7)
a = ap.parse_args()

if a.file.endswith(".json"):
    j = json.load(open(a.file))
    rows = j.get("opportunities") or j.get("deals")
    df = pd.DataFrame([{"opportunity_id": r["opportunity_id"], "amount": r["amount"],
                        "probability": r.get("win_probability", r.get("probability")),
                        "prob_low": (r.get("band") or r.get("historical_band_95ci") or [None, None])[0],
                        "prob_high": (r.get("band") or r.get("historical_band_95ci") or [None, None])[1]} for r in rows])
else:
    df = pd.read_csv(a.file)

rng = np.random.default_rng(a.seed)
amt = df["amount"].values.astype(float)
p = df["probability"].values.astype(float)
lo = df["prob_low"].fillna(df["probability"]).values if "prob_low" in df else p
hi = df["prob_high"].fillna(df["probability"]).values if "prob_high" in df else p

# Per draw: sample each deal's probability within its band (model uncertainty),
# then apply a shared shock on the log-odds scale (correlation between deals).
pp = rng.uniform(lo, hi, size=(a.n, len(p)))
shock = rng.normal(0, a.corr * 2, size=(a.n, 1))
logit = np.log(np.clip(pp, 1e-4, 1 - 1e-4) / (1 - np.clip(pp, 1e-4, 1 - 1e-4))) + shock
wins = rng.random((a.n, len(p))) < 1 / (1 + np.exp(-logit))
tot = a.closed + wins @ amt

res = {"deals": int(len(p)), "closed": a.closed, "expected": round(float(tot.mean())),
       "P10": round(float(np.percentile(tot, 10))), "P50": round(float(np.percentile(tot, 50))),
       "P90": round(float(np.percentile(tot, 90))), "correlation_assumption": a.corr}
if a.commit:
    res["prob_reach_commit"] = round(float((tot >= a.commit).mean()), 3)
if a.quota:
    res["prob_reach_quota"] = round(float((tot >= a.quota).mean()), 3)

# Variance contribution under independence: amount^2 * p * (1 - p).
var = amt ** 2 * p * (1 - p)
top = np.argsort(-var)[:8]
res["swing_deals"] = [{"opportunity_id": df.iloc[i]["opportunity_id"], "amount": float(amt[i]),
                       "probability": float(p[i]), "variance_share": round(float(var[i] / var.sum()), 3)} for i in top]
print(json.dumps(res, indent=2))
