#!/usr/bin/env python3
"""
anomaly_detect.py: robust early-warning detection for time series of account or pipeline metrics.

INPUT CSV: entity_id, period, metric, value   (long format; weekly or monthly)
USAGE: python anomaly_detect.py metrics.csv [--window 12] [--z 3.0] [--min-periods 6]

For each entity and metric, compares the latest value with the entity's own
trailing window using a robust z-score (median and MAD, so one past spike does
not distort the baseline). Also reports a peer z-score (latest value vs the same
metric across all entities in that period) where there are 10 or more peers.
Only flags anomalies; interpretation is left to the skill.
"""
import argparse, json
import numpy as np
import pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument("csv")
ap.add_argument("--window", type=int, default=12)
ap.add_argument("--z", type=float, default=3.0)
ap.add_argument("--min-periods", type=int, default=6)
a = ap.parse_args()

df = pd.read_csv(a.csv)
df["period"] = pd.to_datetime(df["period"], errors="coerce")
df = df.sort_values("period")


def rz(x, ref):
    """Robust z-score of x relative to ref, using median and scaled MAD."""
    med = np.median(ref)
    mad = np.median(np.abs(ref - med)) * 1.4826
    return (x - med) / mad if mad > 0 else 0.0


out = []
for (e, m), g in df.groupby(["entity_id", "metric"]):
    v = g["value"].astype(float).values
    if len(v) < a.min_periods + 1:
        continue
    ref = v[-(a.window + 1):-1]
    z = rz(v[-1], ref)
    last_period = g["period"].iloc[-1]
    peers = df[(df["metric"] == m) & (df["period"] == last_period)]["value"].astype(float).values
    pz = rz(v[-1], peers) if len(peers) >= 10 else None
    if abs(z) >= a.z or (pz is not None and abs(pz) >= a.z):
        out.append({"entity_id": e, "metric": m, "period": str(last_period.date()), "value": float(v[-1]),
                    "baseline_median": float(np.median(ref)), "self_z": round(float(z), 2),
                    "peer_z": None if pz is None else round(float(pz), 2),
                    "direction": "up" if z > 0 else "down"})
print(json.dumps({"threshold_z": a.z, "anomalies": sorted(out, key=lambda d: -abs(d["self_z"]))}, indent=2))
