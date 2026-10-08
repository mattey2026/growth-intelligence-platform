#!/usr/bin/env python3
"""
driver_tree.py: variance and driver decomposition for natural-language BI ("Why is APAC behind plan?").

INPUT CSV at any grain, with actual and plan (or prior) measures and hierarchy columns:
  region, segment, product, account_id, ..., actual, plan[, units_actual, units_plan]
USAGE
  python driver_tree.py data.csv --actual actual --plan plan --levels region segment product account_id \\
     [--filter region=APAC] [--top 3] [--pvm units_actual units_plan] [--out tree.json]

Method:
  1. Total gap = Σ actual − Σ plan (at the filtered scope).
  2. At each level, the contribution of each member = its (actual − plan); the share of gap
     = contribution ÷ total gap. Members are ranked by contribution in the direction of the gap.
  3. Drill recursively into the top contributors (--top) down the level list: the path
     that explains the gap.
  4. Concentration: how many members explain 80% of the gap at each level.
  5. Optional price/volume/mix bridge when unit columns are given:
       volume effect = (units_actual − units_plan) × plan_price
       price effect  = (actual_price − plan_price) × units_actual
Deterministic. It does not claim causes; it locates where the gap sits so the
copilot can investigate why (pipeline, win rate, churn, service, …).
"""
import argparse, json
import pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument("csv")
ap.add_argument("--actual", required=True)
ap.add_argument("--plan", required=True)
ap.add_argument("--levels", nargs="+", required=True)
ap.add_argument("--filter", nargs="*", default=[])
ap.add_argument("--top", type=int, default=3)
ap.add_argument("--pvm", nargs=2)
ap.add_argument("--out")
a = ap.parse_args()

df = pd.read_csv(a.csv)
for f in a.filter:
    k, v = f.split("=", 1)
    df = df[df[k].astype(str) == v]
A, P = df[a.actual].sum(), df[a.plan].sum()
gap = A - P
sign = -1 if gap < 0 else 1


def level(d, lvl):
    g = d.groupby(lvl)[[a.actual, a.plan]].sum()
    g["gap"] = g[a.actual] - g[a.plan]
    g["share_of_gap"] = g["gap"] / gap if gap else 0
    g["attainment_pct"] = (g[a.actual] / g[a.plan] * 100).round(1)
    g = g.sort_values("gap", ascending=(sign < 0))
    cum = (g["gap"] * sign).clip(lower=0).cumsum()
    tot = (g["gap"] * sign).clip(lower=0).sum()
    n80 = int((cum < 0.8 * tot).sum() + 1) if tot > 0 else 0
    return g, n80


def drill(d, lv, depth=0):
    if not lv:
        return []
    g, n80 = level(d, lv[0])
    nodes = []
    for k, r in g.head(a.top).iterrows():
        if r["gap"] * sign <= 0:
            continue
        nodes.append({"level": lv[0], "member": str(k), "actual": round(r[a.actual]), "plan": round(r[a.plan]),
                      "gap": round(r["gap"]), "share_of_gap": round(float(r["share_of_gap"]), 3),
                      "attainment_pct": r["attainment_pct"],
                      "members_explaining_80pct_at_level": n80 if depth == 0 else None,
                      "children": drill(d[d[lv[0]] == k], lv[1:], depth + 1)})
    return nodes


offsets = []
g0, _ = level(df, a.levels[0])
for k, r in g0.iterrows():
    if r["gap"] * sign < 0:
        offsets.append({"member": str(k), "gap": round(r["gap"])})
res = {"scope": a.filter or "all", "actual": round(A), "plan": round(P), "gap": round(gap),
       "attainment_pct": round(A / P * 100, 1) if P else None,
       "path": drill(df, a.levels), "offsetting_members_top_level": offsets}
if a.pvm:
    ua, up = df[a.pvm[0]].sum(), df[a.pvm[1]].sum()
    pp = P / up if up else 0
    pa = A / ua if ua else 0
    res["price_volume_bridge"] = {"volume_effect": round((ua - up) * pp), "price_effect": round((pa - pp) * ua),
                                  "check_sum": round((ua - up) * pp + (pa - pp) * ua), "gap": round(gap)}
print(json.dumps(res, indent=2))
if a.out:
    json.dump(res, open(a.out, "w"), indent=2)
