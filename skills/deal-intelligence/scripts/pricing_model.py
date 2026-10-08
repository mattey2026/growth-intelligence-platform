#!/usr/bin/env python3
"""
pricing_model.py: Price → Discount → Margin → Win probability → Expected value.

USAGE
  python pricing_model.py deal.json --history closed.csv [--controls segment competitor size_band] [--elasticity 0.04 0.08 0.12]

deal.json: {"list_price": 1000000, "unit_cost": 450000, "discounts": [0,5,10,15,20,25],
            "compare": [10, 15], "policy_max_discount": 20, "base_win_prob": 0.35,
            "attributes": {"segment": "Enterprise", "competitor": "CompX"}}

Two modes, chosen automatically and stated in the output:
  A) HISTORICAL model: logistic regression of win on discount + controls. Used only if
     the discount coefficient is positive and significant (|z| ≥ 2) after the controls.
  B) ASSUMPTION mode: in historical deals, discount is usually CONFOUNDED (reps discount
     at-risk deals, so more discount looks associated with losing). If the historical
     coefficient is ≤ 0 or not significant, the effect of discount on winning is not
     identifiable from history. The script then uses stated elasticity assumptions
     (change in win log-odds per discount point, a range), anchored on the deal's
     base win probability (from deal-intelligence), and recommends a controlled test.
For each discount level: net price, margin, p(win), expected revenue = p × net,
expected margin = p × margin, and the policy flag. Also the answer to the "compare"
question, e.g. 10% → 15%.
"""
import argparse, json, math
import numpy as np
import pandas as pd


def fit_logit(X, y, l2=1.0, iters=4000, lr=0.1):
    """Logistic regression with standardized features; returns weights on the original
    scale and approximate z-scores from the Fisher information."""
    mu, sd = X.mean(0), X.std(0) + 1e-9
    Z = (X - mu) / sd
    n, k = Z.shape
    w, b = np.zeros(k), 0.0
    for _ in range(iters):
        p = 1 / (1 + np.exp(-(Z @ w + b)))
        w -= lr * (Z.T @ (p - y) / n + l2 * w / n)
        b -= lr * (p - y).mean()
    p = 1 / (1 + np.exp(-(Z @ w + b)))
    Zb = np.hstack([Z, np.ones((n, 1))])
    H = Zb.T @ (Zb * (p * (1 - p))[:, None]) + np.eye(k + 1) * 1e-6
    se = np.sqrt(np.diag(np.linalg.inv(H)))[:k]
    return w / sd, b - (w * mu / sd).sum(), w / se


ap = argparse.ArgumentParser()
ap.add_argument("deal")
ap.add_argument("--history")
ap.add_argument("--controls", nargs="*", default=[])
ap.add_argument("--elasticity", nargs="*", type=float, default=[0.03, 0.06, 0.10])
a = ap.parse_args()
D = json.load(open(a.deal))
L, C = D["list_price"], D.get("unit_cost")
levels = D.get("discounts", [0, 5, 10, 15, 20, 25])
mode, note, model = "assumption", "", None

if a.history:
    h = pd.read_csv(a.history)
    h = h[h.outcome.isin(["won", "lost"])]
    y = (h.outcome == "won").astype(float).values
    X = pd.DataFrame({"discount_pct": pd.to_numeric(h.discount_pct, errors="coerce").fillna(h.discount_pct.median())})
    for c in a.controls:
        if c in h:
            X = X.join(pd.get_dummies(h[c].fillna("none"), prefix=c, drop_first=True).astype(float))
    cols = list(X.columns)
    w, b, z = fit_logit(X.values.astype(float), y)
    dz, dw = z[0], w[0]
    if dw > 0 and dz >= 2:
        mode = "historical"
        note = f"Discount coefficient positive and significant (z={dz:.1f}) after controls {a.controls}; using the historical model. Still associational; validate with a test."
        attrs = D.get("attributes", {})
        base = np.array([0.0] + [1.0 if any(col == f"{k}_{v}" for k, v in attrs.items()) else 0.0 for col in cols[1:]])
        model = (w, b, base)
    else:
        note = (f"Historical discount coefficient = {dw:+.3f} per point (z={dz:.1f}) after controls {a.controls}. "
                "A non-positive or insignificant effect means discount is confounded with deal risk; its causal effect "
                "on winning cannot be identified from history. Using ASSUMPTION mode with an elasticity range. Recommend a controlled pricing test.")


def p_win(dp, el=None):
    if mode == "historical":
        w, b, base = model
        x = base.copy()
        x[0] = dp
        return 1 / (1 + math.exp(-(x @ w + b)))
    p0 = D.get("base_win_prob", 0.35)
    lo = math.log(p0 / (1 - p0)) + el * dp
    return 1 / (1 + math.exp(-lo))


def table(el=None):
    rows = []
    for dp in levels:
        net = L * (1 - dp / 100)
        pw = p_win(dp, el)
        mg = None if C is None else net - C
        rows.append({"discount_pct": dp, "net_price": round(net), "margin": None if mg is None else round(mg),
                     "margin_pct": None if mg is None else round(mg / net * 100, 1), "p_win": round(pw, 3),
                     "expected_revenue": round(pw * net), "expected_margin": None if mg is None else round(pw * mg),
                     "within_policy": dp <= D.get("policy_max_discount", 100)})
    return rows


out = {"mode": mode, "note": note, "list_price": L, "unit_cost": C, "scenarios": {}}
els = [None] if mode == "historical" else a.elasticity
for el in els:
    t = table(el)
    key = "historical" if el is None else f"elasticity_{el}_logodds_per_pt"
    best_m = max((r for r in t if r["within_policy"] and r["expected_margin"] is not None), key=lambda r: r["expected_margin"], default=None)
    best_r = max((r for r in t if r["within_policy"]), key=lambda r: r["expected_revenue"])
    cmp = None
    if D.get("compare"):
        x, y2 = [r for r in t if r["discount_pct"] in D["compare"]]
        cmp = {"from": x["discount_pct"], "to": y2["discount_pct"], "p_win": [x["p_win"], y2["p_win"]],
               "delta_expected_revenue": y2["expected_revenue"] - x["expected_revenue"],
               "delta_expected_margin": None if x["expected_margin"] is None else y2["expected_margin"] - x["expected_margin"]}
    out["scenarios"][key] = {"table": t, "best_expected_margin_within_policy": best_m["discount_pct"] if best_m else None,
                             "best_expected_revenue_within_policy": best_r["discount_pct"], "compare": cmp}
if mode == "assumption":
    signs = {k: (v["compare"] or {}).get("delta_expected_margin") for k, v in out["scenarios"].items()}
    out["decision_robustness"] = ("Robust: the same direction under all elasticity assumptions"
                                  if len({(s or 0) > 0 for s in signs.values()}) == 1
                                  else "NOT robust: the answer flips depending on the elasticity assumption. Treat as a judgment call; test.")
    out["compare_by_assumption"] = signs
print(json.dumps(out, indent=2))
