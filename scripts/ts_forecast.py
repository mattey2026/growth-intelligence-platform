#!/usr/bin/env python3
"""
ts_forecast.py: period forecast (bookings, revenue, pipeline creation, cases) from a history series.

USAGE: python ts_forecast.py series.csv --date month --value bookings [--freq MS] [--horizon 6] [--season 12]

Methods, chosen by backtest on the last `horizon` periods:
  naive           the last value repeated
  seasonal_naive  the value from the same period last season
  holt_winters    additive level + trend (+ season when there are 2 or more full seasons)
The method with the lowest backtest MAPE is used. Prediction intervals come from
the empirical distribution of backtest errors (80% interval).

Guards: with fewer than 4 periods the script refuses to forecast; with fewer
than 8 it forecasts but warns. The output always includes the naive baseline so
any claimed improvement over it is visible.
"""
import argparse, json
import numpy as np
import pandas as pd


def holt_winters(y, h, season=None, a=0.4, b=0.1, g=0.3):
    """Additive Holt-Winters; falls back to Holt (no season) when history is short."""
    y = np.asarray(y, float)
    n = len(y)
    use_s = season and n >= 2 * season
    L = y[:season].mean() if use_s else y[0]
    T = (y[season:2 * season].mean() - y[:season].mean()) / season if use_s else (y[1] - y[0] if n > 1 else 0)
    S = list(y[:season] - L) if use_s else [0.0]
    for t in range(n):
        s = S[t % season] if use_s else 0
        Lp = L
        L = a * (y[t] - s) + (1 - a) * (L + T)
        T = b * (L - Lp) + (1 - b) * T
        if use_s:
            S[t % season] = g * (y[t] - L) + (1 - g) * s
    return np.array([L + (k + 1) * T + (S[(n + k) % season] if use_s else 0) for k in range(h)])


def forecast(y, h, season, method):
    if method == "naive":
        return np.repeat(y[-1], h)
    if method == "seasonal_naive":
        return np.array([y[-season + (k % season)] for k in range(h)]) if len(y) >= season else np.repeat(y[-1], h)
    return holt_winters(y, h, season)


def mape(a, f):
    a, f = np.asarray(a, float), np.asarray(f, float)
    m = a != 0
    return float(np.mean(np.abs((a[m] - f[m]) / a[m])) * 100) if m.any() else float("nan")


ap = argparse.ArgumentParser()
ap.add_argument("csv")
ap.add_argument("--date", required=True)
ap.add_argument("--value", required=True)
ap.add_argument("--freq", default="MS")
ap.add_argument("--horizon", type=int, default=6)
ap.add_argument("--season", type=int, default=12)
a = ap.parse_args()

df = pd.read_csv(a.csv)
df[a.date] = pd.to_datetime(df[a.date], errors="coerce", format="mixed")
s = df.groupby(pd.Grouper(key=a.date, freq=a.freq))[a.value].sum()
y = s.values.astype(float)
n = len(y)
res = {"periods": n, "from": str(s.index.min())[:10], "to": str(s.index.max())[:10]}
if n < 4:
    res["error"] = "Fewer than 4 periods: no forecast. Describe the data instead."
    print(json.dumps(res, indent=2))
    raise SystemExit
if n < 8:
    res["warning"] = "Fewer than 8 periods: low confidence, trend may be noise."

# Backtest each method on the last hb periods.
hb = min(a.horizon, max(1, n // 4))
tr, te = y[:-hb], y[-hb:]
scores = {m: mape(te, forecast(tr, hb, a.season, m)) for m in ["naive", "seasonal_naive", "holt_winters"]}
best = min(scores, key=lambda m: scores[m] if not np.isnan(scores[m]) else 1e9)
f = forecast(y, a.horizon, a.season, best)

# Empirical error distribution from rolling one-step backtests -> 80% interval.
errs = []
for t in range(max(4, n - 12), n):
    p = forecast(y[:t], 1, a.season, best)[0]
    if y[t] != 0:
        errs.append((y[t] - p) / abs(y[t]))
lo_q, hi_q = (np.quantile(errs, [0.1, 0.9]) if len(errs) >= 5 else (-0.25, 0.25))
idx = pd.date_range(s.index.max(), periods=a.horizon + 1, freq=a.freq)[1:]
res.update({"method": best, "backtest_mape_pct": {k: round(v, 1) for k, v in scores.items()},
            "naive_baseline_mape_pct": round(scores["naive"], 1),
            "forecast": [{"period": str(d)[:10], "point": round(float(v), 2),
                          "p10": round(float(v * (1 + lo_q)), 2), "p90": round(float(v * (1 + hi_q)), 2)} for d, v in zip(idx, f)],
            "interval_basis": "empirical backtest errors" if len(errs) >= 5 else "default ±25% (too few errors)",
            "assumptions": ["History is representative of the horizon", "No structural break (pricing, territory, product)"]})
print(json.dumps(res, indent=2))
