#!/usr/bin/env python3
"""
winloss_analyzer.py: Win/Loss learning engine.

INPUT CSV: closed deals, one row per deal:
  opportunity_id, outcome (won/lost), amount, close_date
  optional factors (any): competitor, loss_reason, industry, region, segment, product,
    size_band, discount_pct, cycle_days, stakeholders_engaged, economic_buyer_engaged,
    champion_strength, proposal_score, ...
USAGE: python winloss_analyzer.py closed.csv --factors competitor industry region size_band economic_buyer_engaged \\
         [--numeric discount_pct cycle_days stakeholders_engaged] [--min-n 15] [--recent-days 180] [--out wl.json]

Outputs:
  base win rate (with 95% Wilson CI)
  per factor level: n, win rate, CI, lift vs base, two-proportion z-test p-value vs the rest,
    and a "reliable" flag (n ≥ min-n and p < 0.05)
  numeric factors: won vs lost medians, and win rate by quartile
  loss-reason Pareto; competitor matrix (encounters, win rate against each)
  drift: recent vs earlier win rate for each factor level (patterns that are changing)
  model_features: reliable factors recommended as features for deal_risk_model / pricing
Associations only. The output labels every pattern "associated with", never "caused".
"""
import argparse, json, math
import pandas as pd


def wilson(k, n, z=1.96):
    if n == 0:
        return [0, 1]
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return [round(max(0, c - h), 3), round(min(1, c + h), 3)]


def ztest(k1, n1, k2, n2):
    """Two-proportion z-test, two-sided p-value."""
    if min(n1, n2) == 0:
        return 1.0
    p = (k1 + k2) / (n1 + n2)
    se = math.sqrt(p * (1 - p) * (1 / n1 + 1 / n2)) or 1e-9
    z = (k1 / n1 - k2 / n2) / se
    return round(math.erfc(abs(z) / math.sqrt(2)), 4)


ap = argparse.ArgumentParser()
ap.add_argument("csv")
ap.add_argument("--factors", nargs="*", default=[])
ap.add_argument("--numeric", nargs="*", default=[])
ap.add_argument("--min-n", type=int, default=15)
ap.add_argument("--recent-days", type=int, default=180)
ap.add_argument("--out")
a = ap.parse_args()
df = pd.read_csv(a.csv)
df = df[df.outcome.isin(["won", "lost"])].copy()
df["w"] = (df.outcome == "won").astype(int)
N, K = len(df), int(df.w.sum())
res = {"closed_deals": N, "base_win_rate": round(K / N, 3), "base_ci": wilson(K, N), "factors": {}, "numeric": {}}
if "close_date" in df:
    df["close_date"] = pd.to_datetime(df.close_date, errors="coerce", format="mixed")
    recent = df.close_date >= df.close_date.max() - pd.Timedelta(days=a.recent_days)
else:
    recent = pd.Series(False, index=df.index)
feats = []
for f in a.factors:
    if f not in df:
        continue
    rows = []
    for lvl, g in df.groupby(f):
        n, k = len(g), int(g.w.sum())
        rest = df[df[f] != lvl]
        p = ztest(k, n, int(rest.w.sum()), len(rest))
        rn = g[recent.loc[g.index]]
        en = g[~recent.loc[g.index]]
        rows.append({"level": str(lvl), "n": n, "win_rate": round(k / n, 3), "ci": wilson(k, n),
                     "lift_vs_base": round((k / n) / (K / N), 2) if K else None, "p_value": p,
                     "reliable": n >= a.min_n and p < 0.05,
                     "recent_win_rate": round(rn.w.mean(), 3) if len(rn) >= 5 else None,
                     "earlier_win_rate": round(en.w.mean(), 3) if len(en) >= 5 else None})
    rows.sort(key=lambda r: -r["n"])
    res["factors"][f] = rows
    if any(r["reliable"] for r in rows):
        feats.append(f)
for f in a.numeric:
    if f not in df:
        continue
    x = pd.to_numeric(df[f], errors="coerce")
    q = pd.qcut(x, 4, duplicates="drop")
    res["numeric"][f] = {"won_median": float(x[df.w == 1].median()), "lost_median": float(x[df.w == 0].median()),
                         "win_rate_by_quartile": {str(k): round(v, 3) for k, v in df.groupby(q, observed=True).w.mean().items()}}
    feats.append(f)
if "loss_reason" in df:
    lr = df[df.w == 0].loss_reason.fillna("unrecorded").value_counts()
    res["loss_reason_pareto"] = [{"reason": k, "count": int(v), "share": round(v / lr.sum(), 3)} for k, v in lr.items()]
    res["loss_reason_completeness"] = round(1 - (df[df.w == 0].loss_reason.isna().mean()), 3)
if "competitor" in df:
    cm = []
    for c, g in df[df.competitor.notna()].groupby("competitor"):
        cm.append({"competitor": c, "encounters": len(g), "our_win_rate": round(g.w.mean(), 3), "ci": wilson(int(g.w.sum()), len(g)),
                   "lost_value": round(float(g[g.w == 0].amount.sum())) if "amount" in g else None})
    res["competitor_matrix"] = sorted(cm, key=lambda r: -r["encounters"])
res["model_features_recommended"] = feats
res["caution"] = "Associations, not causes. Confirm with win/loss interviews before changing the sales strategy; use experiments for pricing."
print(json.dumps(res, indent=2, default=str))
if a.out:
    json.dump(res, open(a.out, "w"), indent=2, default=str)
