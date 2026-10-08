#!/usr/bin/env python3
"""
propensity_model.py: general explainable propensity model shared by skills in this plugin.

Used for renewal/churn risk, expansion propensity, account conversion propensity,
RFP bid-win probability, approval-as-submitted likelihood, and similar outcomes.
Dependencies: numpy and pandas only.

USAGE
  python propensity_model.py backtest data.csv --id account_id --date as_of_date --label churned \
         --features util_trend_90d cases_qoq sev12_open days_overdue nps sponsor_changed
  python propensity_model.py score data.csv --id account_id --date as_of_date --label churned \
         --features ... --out scores.json

Rows with a label of 0 or 1 are history; rows with a blank label are scored.
With fewer than 200 labelled rows the script refuses to fit a model and reports
historical base rates only (Low confidence).
"""
import argparse, json
import numpy as np
import pandas as pd

MIN_LABELLED = 200

class Model:
    """L2-regularized logistic regression on standardized features, trained by gradient descent."""

    def fit(self, X, y, l2=1.0, iters=3000, lr=0.1):
        self.med = np.nanmedian(X, axis=0)
        X = np.where(np.isnan(X), self.med, X)
        self.mu, self.sd = X.mean(0), X.std(0) + 1e-9
        Z = (X - self.mu) / self.sd
        n, k = Z.shape
        w, b = np.zeros(k), 0.0
        for _ in range(iters):
            p = 1 / (1 + np.exp(-(Z @ w + b)))
            w -= lr * (Z.T @ (p - y) / n + l2 * w / n)
            b -= lr * (p - y).mean()
        self.w, self.b = w, b
        return self

    def z(self, X):
        X = np.where(np.isnan(X), self.med, X)
        return (X - self.mu) / self.sd

    def predict(self, X):
        return 1 / (1 + np.exp(-(self.z(X) @ self.w + self.b)))

    def contributions(self, X):
        # Per-feature contribution to the log-odds, relative to an average deal.
        return self.z(X) * self.w


def auc(y, p):
    """Area under the ROC curve via rank statistics (handles ties)."""
    y = np.asarray(y)
    r = pd.Series(p).rank().values
    pos = y == 1
    n1, n0 = pos.sum(), (~pos).sum()
    if n1 == 0 or n0 == 0:
        return float("nan")
    return (r[pos].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


def wilson(k, n, z=1.96):
    """95% Wilson score interval for k successes in n trials."""
    if n == 0:
        return (0.0, 1.0)
    ph = k / n
    d = 1 + z * z / n
    c = (ph + z * z / (2 * n)) / d
    h = z * np.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / d
    return (max(0, c - h), min(1, c + h))


def calibration(y, p, bins=5):
    """Compare predicted vs observed rates in probability buckets."""
    edges = np.linspace(0, 1, bins + 1)
    out = []
    for i in range(bins):
        m = (p >= edges[i]) & (p < edges[i + 1] if i < bins - 1 else p <= 1)
        n = int(m.sum())
        k = int(np.asarray(y)[m].sum()) if n else 0
        lo, hi = wilson(k, n)
        out.append({"bin": f"{edges[i]:.1f}-{edges[i+1]:.1f}", "n": n,
                    "mean_pred": round(float(p[m].mean()), 3) if n else None,
                    "observed": round(k / n, 3) if n else None,
                    "observed_95ci": [round(lo, 3), round(hi, 3)]})
    return out


def confidence_label(auc_v, n_bin, n_train):
    if n_train < MIN_LABELLED or np.isnan(auc_v) or auc_v < 0.65 or n_bin < 20:
        return "Low"
    if auc_v >= 0.75 and n_bin >= 50:
        return "High"
    return "Medium"



def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["backtest", "score"])
    ap.add_argument("csv")
    ap.add_argument("--id", required=True)
    ap.add_argument("--date", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--features", nargs="+", required=True)
    ap.add_argument("--amount", help="optional value column for value-at-risk")
    ap.add_argument("--out")
    a = ap.parse_args()

    df = pd.read_csv(a.csv)
    df[a.date] = pd.to_datetime(df[a.date], errors="coerce")
    feats = [f for f in a.features if f in df.columns]
    for f in feats:
        df[f] = pd.to_numeric(df[f], errors="coerce")
    df["y"] = pd.to_numeric(df[a.label], errors="coerce")
    lab = df.dropna(subset=["y"]).sort_values(a.date)
    res = {"label": a.label, "features_used": feats, "labelled_rows": int(len(lab)),
           "base_rate": round(float(lab["y"].mean()), 3) if len(lab) else None}

    # Thin history: report base rates only, never a fitted model.
    if len(lab) < MIN_LABELLED:
        k, n = int(lab["y"].sum()), len(lab)
        res.update({"method": "base_rate_only", "base_rate_95ci": [round(x, 3) for x in wilson(k, n)],
                    "note": f"Only {n} labelled rows; no model fitted. Use rules plus evidence; confidence Low."})
        print(json.dumps(res, indent=2, default=str))
        if a.out:
            json.dump(res, open(a.out, "w"), indent=2, default=str)
        return

    # Time-based split by entity: older entities train, newer entities test.
    first = lab.groupby(a.id)[a.date].min().sort_values()
    test_ids = set(first.index[int(len(first) * 0.7):])
    tr, te = lab[~lab[a.id].isin(test_ids)], lab[lab[a.id].isin(test_ids)]
    mh = Model().fit(tr[feats].values, tr["y"].values)
    ph = mh.predict(te[feats].values)
    auc_v = auc(te["y"].values, ph)
    cal = calibration(te["y"].values, ph)
    top = ph >= np.quantile(ph, 0.8)
    res.update({"method": "logistic_regression_l2",
                "backtest": {"auc": round(auc_v, 3),
                             "brier": round(float(np.mean((ph - te["y"].values) ** 2)), 4),
                             "brier_base_rate": round(float(np.mean((te["y"].mean() - te["y"].values) ** 2)), 4),
                             "top20pct_capture": round(float(te["y"].values[top].sum() / max(te["y"].sum(), 1)), 3),
                             "calibration": cal}})
    m = Model().fit(lab[feats].values, lab["y"].values)
    res["global_drivers"] = sorted([{"feature": f, "weight": round(float(w), 3)} for f, w in zip(feats, m.w)],
                                   key=lambda d: -abs(d["weight"]))
    if a.mode == "score":
        cur = df[df["y"].isna()].sort_values(a.date).groupby(a.id).tail(1)
        P, C = m.predict(cur[feats].values), m.contributions(cur[feats].values)
        rows = []
        for i, (_, r) in enumerate(cur.iterrows()):
            cb = cal[min(int(P[i] * 5), 4)]
            order = np.argsort(-np.abs(C[i]))[:4]
            d = {"id": r[a.id], "probability": round(float(P[i]), 3), "historical_band_95ci": cb["observed_95ci"],
                 "confidence": confidence_label(auc_v, cb["n"], len(lab)),
                 "top_factors": [{"factor": feats[j], "value": None if pd.isna(r[feats[j]]) else float(r[feats[j]]),
                                  "direction": "raises" if C[i][j] > 0 else "lowers",
                                  "strength": round(float(abs(C[i][j])), 2)} for j in order]}
            if a.amount and a.amount in cur.columns:
                d["value_at_risk"] = round(float(P[i] * r[a.amount]), 2)
            rows.append(d)
        res["scored"] = sorted(rows, key=lambda x: -x["probability"])
    print(json.dumps(res, indent=2, default=str))
    if a.out:
        json.dump(res, open(a.out, "w"), indent=2, default=str)


if __name__ == "__main__":
    main()
