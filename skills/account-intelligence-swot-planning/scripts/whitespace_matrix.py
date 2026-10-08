#!/usr/bin/env python3
"""
whitespace_matrix.py: evidence-based whitespace sizing and prioritization.

INPUT CSV (long format, one row per account × offering, the install base across
the customer base):
  account_id, segment, offering, revenue           (revenue = annual spend with us; 0 or absent = not owned)
Optional columns: dimension (product | business_unit | geography | capability), fit_signal (0-1)
Optional --propensity scores.json: output of propensity_model.py
  ({"scored":[{"id":..., "probability":...}]}) keyed by account_id or "account|offering"

USAGE: python whitespace_matrix.py install_base.csv --account ACME [--min-peers 8] [--out ws.json]

Method (deterministic, explainable):
  peers              = accounts in the same segment that own the offering
  adoption_rate      = share of segment accounts that own the offering
  peer_median_spend  = median revenue on that offering among peer owners
  potential          = max(peer_median_spend − current_spend, 0), and for a
                       partial owner the gap to the peer median
  probability        = propensity score if provided; else adoption_rate (a
                       base-rate proxy, labelled as such)
  expected_value     = potential × probability
  priority_score     = expected_value × (0.5 + 0.5 × fit_signal)   (fit defaults to 0.5)
Offerings with fewer than --min-peers owners are reported as "insufficient peer
evidence" and are not sized.
"""
import argparse, json
import numpy as np
import pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument("csv")
ap.add_argument("--account", required=True)
ap.add_argument("--min-peers", type=int, default=8)
ap.add_argument("--propensity")
ap.add_argument("--out")
a = ap.parse_args()

df = pd.read_csv(a.csv)
df["revenue"] = pd.to_numeric(df["revenue"], errors="coerce").fillna(0)
if "dimension" not in df:
    df["dimension"] = "product"
acc = df[df.account_id.astype(str) == str(a.account)]
if acc.empty:
    raise SystemExit(json.dumps({"error": f"account {a.account} not in install base"}))
seg = acc["segment"].iloc[0]
segdf = df[df.segment == seg]
n_seg = segdf.account_id.nunique()
fit = dict(zip(acc.offering, acc.get("fit_signal", pd.Series([np.nan] * len(acc)))))

prop = {}
if a.propensity:
    for r in json.load(open(a.propensity)).get("scored", []):
        prop[str(r["id"])] = r["probability"]

rows, insufficient = [], []
for (dim, off), g in segdf.groupby(["dimension", "offering"]):
    owners = g[g.revenue > 0]
    cur = float(acc[(acc.offering == off)]["revenue"].sum())
    if len(owners) < a.min_peers:
        if cur == 0:
            insufficient.append({"offering": off, "dimension": dim, "peer_owners": int(len(owners))})
        continue
    med = float(owners.revenue.median())
    pot = max(med - cur, 0.0)
    if pot <= 0:
        continue
    adopt = owners.account_id.nunique() / n_seg
    p = prop.get(f"{a.account}|{off}", prop.get(str(a.account)))
    basis = "propensity model" if p is not None else "segment adoption rate (base-rate proxy)"
    p = p if p is not None else adopt
    f = fit.get(off)
    f = 0.5 if f is None or pd.isna(f) else float(f)
    ev = pot * p
    rows.append({"offering": off, "dimension": dim, "status": "expand" if cur > 0 else "whitespace",
                 "current_spend": round(cur), "peer_median_spend": round(med), "peer_owners": int(len(owners)),
                 "segment_adoption_rate": round(adopt, 3), "potential": round(pot),
                 "probability": round(float(p), 3), "probability_basis": basis, "fit_signal": f,
                 "expected_value": round(ev), "priority_score": round(ev * (0.5 + 0.5 * f))})

rows.sort(key=lambda r: -r["priority_score"])
res = {"account": a.account, "segment": seg, "segment_accounts": int(n_seg),
       "current_total_spend": round(float(acc.revenue.sum())),
       "total_potential": round(sum(r["potential"] for r in rows)),
       "total_expected_value": round(sum(r["expected_value"] for r in rows)),
       "opportunities": rows, "insufficient_peer_evidence": insufficient,
       "assumptions": ["Peer median spend approximates attainable spend for this account",
                       "Segment peers are comparable (size, industry)",
                       "Adoption rate is a base-rate proxy for probability when no propensity model is provided"]}
print(json.dumps(res, indent=2))
if a.out:
    json.dump(res, open(a.out, "w"), indent=2)
