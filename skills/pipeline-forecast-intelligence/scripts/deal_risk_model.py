#!/usr/bin/env python3
"""
deal_risk_model.py: explainable deal win and slippage prediction for the deal-risk-intelligence skill.

Dependencies: numpy and pandas only, so it runs in restricted sandboxes.

MODES
  backtest  Train on older snapshots and test on newer ones (time-based split).
            Reports AUC, Brier score, calibration, and lift, and compares against
            a naive baseline (the seller's forecast category).
  score     Fit on all labelled history, then score open deals.
            Writes a probability, a probability band, a confidence label, and
            the top factors driving each prediction.

INPUT CSV (one row per opportunity snapshot; weekly snapshots are ideal)
  Required: opportunity_id, snapshot_date, close_date, amount, stage_index, outcome
    outcome        : won | lost | open
    closed_on_time : 1/0/blank (1 = closed-won on or before the close date
                     recorded at snapshot time; required for --target slip)
  Optional feature columns (any subset; missing columns are ignored):
    days_in_stage, close_date_pushes, days_since_buyer_activity,
    buyer_contacts_engaged, economic_buyer_engaged, paper_process_started,
    competitor_present, deal_age_days, amount_change_pct, forecast_commit
  Use --features to add any other numeric column.

If there are fewer than MIN_LABELLED labelled rows, the script falls back to
transparent rule-based scoring and says so. It never presents a weak model as
reliable.
"""
import argparse, json, sys
import numpy as np
import pandas as pd

MIN_LABELLED = 200
DEFAULT_FEATURES = ["stage_index", "days_in_stage", "close_date_pushes", "days_since_buyer_activity",
                    "buyer_contacts_engaged", "economic_buyer_engaged", "paper_process_started",
                    "competitor_present", "deal_age_days", "amount_change_pct", "log_amount",
                    "days_to_close", "forecast_commit"]
LABELS = {
    "stage_index": "stage", "days_in_stage": "days in current stage", "close_date_pushes": "close-date pushes",
    "days_since_buyer_activity": "days since buyer activity", "buyer_contacts_engaged": "engaged buyer contacts",
    "economic_buyer_engaged": "economic buyer engaged", "paper_process_started": "paper process started",
    "competitor_present": "competitor present", "deal_age_days": "deal age", "amount_change_pct": "amount change %",
    "log_amount": "deal size", "days_to_close": "days to close date", "forecast_commit": "seller commit flag"}


def prepare(df, target, extra):
    """Parse dates, derive features, and build the target column."""
    df = df.copy()
    for c in ["snapshot_date", "close_date"]:
        df[c] = pd.to_datetime(df[c], errors="coerce")
    df["log_amount"] = np.log1p(pd.to_numeric(df["amount"], errors="coerce").fillna(0))
    df["days_to_close"] = (df["close_date"] - df["snapshot_date"]).dt.days
    feats = [f for f in DEFAULT_FEATURES + (extra or []) if f in df.columns]
    for f in feats:
        df[f] = pd.to_numeric(df[f], errors="coerce")
    if target == "win":
        df["y"] = df["outcome"].map({"won": 1, "lost": 0})
    else:  # slip: 1 = the deal did NOT close-won by its committed date
        df["y"] = np.where(df["outcome"] == "open", np.nan,
                           1 - pd.to_numeric(df.get("closed_on_time"), errors="coerce"))
    return df, feats


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


def rules_score(row, target):
    """Transparent points-based fallback used when history is too thin for a model."""
    pts, why = 0, []
    def g(c):
        v = row.get(c)
        return None if v is None or (isinstance(v, float) and np.isnan(v)) else v
    checks = [
        (g("close_date_pushes") is not None and g("close_date_pushes") >= 2, 2, "close date pushed 2+ times"),
        (g("days_since_buyer_activity") is not None and g("days_since_buyer_activity") > 21, 2, "no buyer activity in 21+ days"),
        (g("economic_buyer_engaged") == 0, 2, "economic buyer not engaged"),
        (g("paper_process_started") == 0 and g("days_to_close") is not None and g("days_to_close") <= 30, 2, "close date within 30 days, no paper process"),
        (g("buyer_contacts_engaged") is not None and g("buyer_contacts_engaged") <= 1, 1, "single-threaded"),
        (g("competitor_present") == 1, 1, "competitor present"),
    ]
    for cond, p, label in checks:
        if cond:
            pts += p
            why.append(label)
    risk = "High" if pts >= 5 else "Medium" if pts >= 3 else "Low"
    return risk, pts, why


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["backtest", "score"])
    ap.add_argument("csv")
    ap.add_argument("--target", choices=["win", "slip"], default="slip")
    ap.add_argument("--features", nargs="*")
    ap.add_argument("--test-frac", type=float, default=0.3)
    ap.add_argument("--out")
    a = ap.parse_args()

    df, feats = prepare(pd.read_csv(a.csv), a.target, a.features)
    lab = df.dropna(subset=["y"]).sort_values("snapshot_date")
    res = {"target": a.target, "features_used": feats, "labelled_rows": int(len(lab)),
           "labelled_opportunities": int(lab["opportunity_id"].nunique())}

    # Thin history: refuse to fit a model and fall back to transparent rules.
    if len(lab) < MIN_LABELLED:
        res["method"] = "rules_fallback"
        res["note"] = (f"Only {len(lab)} labelled rows (< {MIN_LABELLED}). "
                       "A statistical model would be unreliable; using transparent rules. "
                       "Treat all outputs as Low confidence.")
        if a.mode == "score":
            open_ = df[df["outcome"] == "open"].sort_values("snapshot_date").groupby("opportunity_id").tail(1)
            res["deals"] = []
            for _, r in open_.iterrows():
                risk, pts, why = rules_score(r.to_dict(), a.target)
                res["deals"].append({"opportunity_id": r["opportunity_id"], "amount": float(r["amount"]),
                                     "risk": risk, "points": pts, "factors": why, "confidence": "Low"})
        print(json.dumps(res, indent=2, default=str))
        if a.out:
            json.dump(res, open(a.out, "w"), indent=2, default=str)
        return

    res["method"] = "logistic_regression_l2"
    if a.mode == "backtest":
        # Split by opportunity (not by row) so snapshots of one deal never land
        # on both sides, and by time (older deals train, newer deals test).
        first = lab.groupby("opportunity_id")["snapshot_date"].min().sort_values()
        cut_ids = set(first.index[int(len(first) * (1 - a.test_frac)):])
        tr, te = lab[~lab.opportunity_id.isin(cut_ids)], lab[lab.opportunity_id.isin(cut_ids)]
        m = Model().fit(tr[feats].values, tr["y"].values)
        p = m.predict(te[feats].values)
        y = te["y"].values
        res["backtest"] = {"train_rows": int(len(tr)), "test_rows": int(len(te)),
                           "auc": round(auc(y, p), 3),
                           "brier": round(float(np.mean((p - y) ** 2)), 4),
                           "brier_base_rate": round(float(np.mean((y.mean() - y) ** 2)), 4),
                           "calibration": calibration(y, p)}
        # Naive baseline: the seller's own commit flag, if present.
        if "forecast_commit" in te.columns and te["forecast_commit"].notna().any():
            fc = te["forecast_commit"].fillna(0).values
            naive = (1 - fc) if a.target == "slip" else fc
            res["backtest"]["baseline_seller_commit_auc"] = round(auc(y, naive + 1e-6 * np.random.rand(len(naive))), 3)
        # Lift: share of positives captured in the top 20% riskiest predictions.
        top = p >= np.quantile(p, 0.8)
        res["backtest"]["top20pct_capture"] = round(float(y[top].sum() / max(y.sum(), 1)), 3)
        res["global_drivers"] = sorted([{"feature": LABELS.get(f, f), "weight": round(float(w), 3)}
                                        for f, w in zip(feats, m.w)], key=lambda d: -abs(d["weight"]))
    else:
        # Fit on all history, keep a time-held-out slice to set confidence labels.
        first = lab.groupby("opportunity_id")["snapshot_date"].min().sort_values()
        cut_ids = set(first.index[int(len(first) * 0.8):])
        hold = lab[lab.opportunity_id.isin(cut_ids)]
        m_hold = Model().fit(lab[~lab.opportunity_id.isin(cut_ids)][feats].values,
                             lab[~lab.opportunity_id.isin(cut_ids)]["y"].values)
        ph = m_hold.predict(hold[feats].values)
        auc_v = auc(hold["y"].values, ph)
        cal = calibration(hold["y"].values, ph)
        m = Model().fit(lab[feats].values, lab["y"].values)
        open_ = df[df["outcome"] == "open"].sort_values("snapshot_date").groupby("opportunity_id").tail(1)
        P = m.predict(open_[feats].values)
        C = m.contributions(open_[feats].values)
        deals = []
        for i, (_, r) in enumerate(open_.iterrows()):
            b = min(int(P[i] * 5), 4)
            cb = cal[b]
            order = np.argsort(-np.abs(C[i]))[:4]
            factors = [{"factor": LABELS.get(feats[j], feats[j]),
                        "value": None if pd.isna(r[feats[j]]) else float(r[feats[j]]),
                        "direction": ("raises" if C[i][j] > 0 else "lowers") + f" {a.target} probability",
                        "strength": round(float(abs(C[i][j])), 2)} for j in order]
            deals.append({"opportunity_id": r["opportunity_id"], "amount": float(r["amount"]),
                          "probability": round(float(P[i]), 3),
                          "historical_band_95ci": cb["observed_95ci"],
                          "confidence": confidence_label(auc_v, cb["n"], len(lab)),
                          "top_factors": factors})
        res.update({"holdout_auc": round(auc_v, 3), "calibration": cal,
                    "deals": sorted(deals, key=lambda d: -d["probability"])})
    print(json.dumps(res, indent=2, default=str))
    if a.out:
        json.dump(res, open(a.out, "w"), indent=2, default=str)


if __name__ == "__main__":
    main()
