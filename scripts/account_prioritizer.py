#!/usr/bin/env python3
"""
account_prioritizer.py: transparent multi-criteria account prioritization.

INPUT CSV: account_id plus one numeric column per criterion (any names), e.g.
  existing_revenue, growth_potential, expansion_propensity, health, strategic_importance,
  relationship_strength, competitive_position, risk, whitespace, conversion_probability
CONFIG JSON (--config): {"weights": {"growth_potential": 0.25, ...},
                         "higher_is_better": {"risk": false}}   # criteria where lower is better

USAGE: python account_prioritizer.py accounts.csv --config weights.json [--out pri.json]

Method:
  1. Each criterion is min-max normalized to 0-1 across the accounts supplied
     (inverted where lower is better).
  2. The weighted sum gives the composite score; the per-criterion contributions
     are reported for every account (the drivers).
  3. Tiers are assigned by composite score.
  4. Rank stability: 500 random weight perturbations (±30%); each account's
     rank range and the share of runs in which it stays in the top quartile.
     This shows whether a ranking is robust or an artefact of the chosen weights.
Missing criterion values are imputed with the median and flagged per account.
"""
import argparse, json
import numpy as np
import pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument("csv")
ap.add_argument("--config", required=True)
ap.add_argument("--out")
a = ap.parse_args()

cfg = json.load(open(a.config))
W = cfg["weights"]
hib = cfg.get("higher_is_better", {})
df = pd.read_csv(a.csv)
crit = [c for c in W if c in df.columns]
missing_cfg = [c for c in W if c not in df.columns]
flags = {r: [c for c in crit if pd.isna(df.loc[i, c])] for i, r in enumerate(df.account_id)}
X = df[crit].apply(pd.to_numeric, errors="coerce")
X = X.fillna(X.median())
N = (X - X.min()) / (X.max() - X.min()).replace(0, 1)
for c in crit:
    if not hib.get(c, True):
        N[c] = 1 - N[c]
w = np.array([W[c] for c in crit], float)
w = w / w.sum()
contrib = N.values * w
score = contrib.sum(1)

# Rank stability under random ±30% weight perturbations.
rng = np.random.default_rng(11)
ranks = []
for _ in range(500):
    wp = w * rng.uniform(0.7, 1.3, len(w))
    wp /= wp.sum()
    s = N.values @ wp
    ranks.append((-s).argsort().argsort() + 1)
ranks = np.array(ranks)
q = max(1, len(df) // 4)

out = []
base_rank = (-score).argsort().argsort() + 1
for i, acc in enumerate(df.account_id):
    order = np.argsort(-contrib[i])
    out.append({"account_id": acc, "rank": int(base_rank[i]), "score": round(float(score[i]), 3),
                "tier": "A" if score[i] >= np.quantile(score, 0.75) else "B" if score[i] >= np.quantile(score, 0.4) else "C",
                "top_drivers": [{"criterion": crit[j], "normalized": round(float(N.values[i, j]), 2),
                                 "contribution": round(float(contrib[i, j]), 3)} for j in order[:3]],
                "weakest": [crit[j] for j in order[-2:]],
                "rank_range_under_weight_changes": [int(ranks[:, i].min()), int(ranks[:, i].max())],
                "top_quartile_stability": round(float((ranks[:, i] <= q).mean()), 2),
                "imputed_criteria": flags[acc]})
out.sort(key=lambda r: r["rank"])
res = {"criteria": crit, "weights_normalized": dict(zip(crit, np.round(w, 3).tolist())),
       "criteria_in_config_but_missing_in_data": missing_cfg, "accounts": out,
       "note": "Scores are relative to the accounts supplied. Read the drivers and stability, not just the rank."}
print(json.dumps(res, indent=2))
if a.out:
    json.dump(res, open(a.out, "w"), indent=2)
