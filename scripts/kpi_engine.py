#!/usr/bin/env python3
"""
kpi_engine.py: adaptive KPI engine.

Chooses the KPI framework from the Business Context Profile (B2B, B2G, D2C/B2C) and
computes ONLY the KPIs the data supports. Unsupported KPIs are listed with the missing
input, never estimated. When a previous KPI snapshot is supplied (from the memory graph),
each KPI shows current vs previous, change, and whether the forecast moved.

USAGE: python kpi_engine.py data.xlsx --profile profile.json [--previous kpis_prev.json]
         [--targets targets.json] [--benchmarks bench.json] [--asof 2026-09-29] [--out kpis.json]
Output per KPI: name, value, unit, formula, source, status (actual | unsupported), previous,
change_pct, target, benchmark, variance.
"""
import argparse, json, re
import pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument("data"); ap.add_argument("--profile", required=True); ap.add_argument("--previous"); ap.add_argument("--targets")
ap.add_argument("--benchmarks"); ap.add_argument("--asof", default=str(pd.Timestamp.today().date())); ap.add_argument("--out")
a = ap.parse_args()
T = pd.read_excel(a.data, sheet_name=None) if a.data.lower().endswith((".xlsx", ".xls")) else {"data": pd.read_csv(a.data)}
T = {k: v for k, v in T.items() if not re.search(r"readme|test|expected|result|summary", k, re.I)}
prof = json.load(open(a.profile)); model = prof["kpi_framework"]["model"]
prev = {k["name"]: k for k in json.load(open(a.previous))["kpis"]} if a.previous else {}
tgt = json.load(open(a.targets)) if a.targets else {}
bm = json.load(open(a.benchmarks)) if a.benchmarks else {}
asof = pd.Timestamp(a.asof)

def col(pat, sheet_pat=None, numeric=True):
    for s, df in T.items():
        if sheet_pat and not re.search(sheet_pat, s, re.I):
            continue
        for c in df.columns:
            if re.search(pat, str(c), re.I) and (not numeric or pd.api.types.is_numeric_dtype(df[c])):
                return s, c, df
    return None, None, None

K = []
def add(name, value, unit, formula, source, fmt=None):
    K.append({"name": name, "value": None if value is None else round(float(value), 4), "unit": unit, "formula": formula, "source": source, "status": "actual"})
def missing(name, needs):
    K.append({"name": name, "value": None, "status": "unsupported", "needs": needs})

if model in ("B2B", "B2G"):
    s, rc, df = col(r"current_revenue|annual_revenue|contract_value|arr", r"account|financ|contract")
    if rc:
        r = df[rc]; add("Contracted revenue", r.sum(), "$", f"SUM({s}.{rc})", s)
        add("Top-account concentration", r.max() / r.sum(), "%", "max(account revenue) ÷ total", s)
        add("Top-3 concentration", r.nlargest(3).sum() / r.sum(), "%", "top-3 revenue ÷ total", s)
    s2, gp, fdf = col(r"gross_profit", r"financ")
    s3, cts, _ = col(r"cost_to_serve", r"financ")
    s4, frev, _ = col(r"annual_revenue", r"financ")
    if gp and frev:
        add("Gross margin", fdf[gp].sum() / fdf[frev].sum(), "%", "Σ gross profit ÷ Σ revenue", s2)
    if gp and cts and frev:
        add("Contribution margin", (fdf[gp].sum() - fdf[cts].sum()) / fdf[frev].sum(), "%", "(Σ GP − Σ cost to serve) ÷ Σ revenue", s2)
        add("Cost to serve", fdf[cts].sum() / fdf[frev].sum(), "%", "Σ cost to serve ÷ Σ revenue", s3)
    so, am, odf = col(r"^amount$|deal_value", r"opportunit")
    if am:
        stc = [c for c in odf.columns if re.search(r"^stage$|^status$", str(c), re.I)]
        allo = odf
        closed_mask = allo[stc].astype(str).apply(lambda s: s.str.contains("closed|won|lost", case=False)).any(axis=1) if stc else pd.Series(False, index=allo.index)
        won_mask = allo[stc].astype(str).apply(lambda s: s.str.contains("won", case=False)).any(axis=1) if stc else pd.Series(False, index=allo.index)
        odf = allo[~closed_mask]
        if won_mask.any():
            add("Bookings (closed won, in data)", allo.loc[won_mask, am].sum(), "$", "Σ amount where stage/status = Won", so)
    sp, pr, _ = col(r"win_prob|probability", r"opportunit")
    if am:
        add("Open pipeline", odf[am].sum(), "$", f"SUM({so}.{am})", so)
        add("Average deal size (ACV proxy)", odf[am].mean(), "$", "mean open deal amount", so)
        if pr:
            add("Weighted pipeline", (odf[am] * odf[pr]).sum(), "$", "Σ amount × CRM probability", so)
        oc = [c for c in odf.columns if re.search(r"original_close", c, re.I)]; cc = [c for c in odf.columns if re.search(r"current_close", c, re.I)]
        if oc and cc:
            sl = pd.to_datetime(odf[cc[0]]) > pd.to_datetime(odf[oc[0]])
            add("Slipped pipeline share", odf.loc[sl, am].sum() / odf[am].sum(), "%", "Σ amount of deals whose close date moved later ÷ pipeline", so)
        if "target" in tgt:
            add("Pipeline coverage", odf[am].sum() / tgt["target"], "x", "open pipeline ÷ period target", "targets")
        else:
            missing("Pipeline coverage", "a period target or quota")
    stg = col(r"stage|status|outcome", r"opportunit", numeric=False)
    closed = stg[2] is not None and stg[2][stg[1]].astype(str).str.contains("won|lost", case=False).any()
    if stg[2] is not None:
        sv = stg[2][stg[1]].astype(str).str.lower()
        nw, nl = int(sv.str.contains("won").sum()), int(sv.str.contains("lost").sum())
        if nw + nl >= 10 and nl > 0:
            add("Win rate", nw / (nw + nl), "%", "won ÷ (won + lost)", stg[0])
        else:
            missing("Win rate", f"at least 10 closed outcomes including losses (have {nw} won, {nl} lost)")
    sc, ex, cdf = col(r"expiry|end_date|renewal_date", r"contract", numeric=False)
    if ex:
        d = (pd.to_datetime(cdf[ex]) - asof).dt.days
        _, cv, _ = col(r"contract_value|value", r"contract")
        add("Renewal exposure (≤90 days)", cdf.loc[d.between(0, 90), cv].sum(), "$", "Σ contract value expiring within 90 days", sc)
        add("Renewal exposure (≤180 days)", cdf.loc[d.between(0, 180), cv].sum(), "$", "Σ contract value expiring within 180 days", sc)
        rr = [c for c in cdf.columns if re.search(r"renewal_risk", c, re.I)]
        if rr:
            add("Revenue under high renewal risk", cdf.loc[cdf[rr[0]].astype(str).str.lower() == "high", cv].sum(), "$", "Σ contract value where renewal risk = High", sc)
    missing("Net revenue retention (NRR)", "prior-period revenue per customer (two revenue snapshots)")
    missing("Gross revenue retention (GRR)", "prior-period revenue per customer")
    missing("CAC / CAC payback", "sales and marketing cost by period (only campaign spend is present)")
    sp2, disc, pdf = col(r"discount_pct", r"pric")
    lp = col(r"list_price", r"pric")[1]; ap_ = col(r"actual_price", r"pric")[1]
    if lp and ap_:
        add("Realized discount", 1 - pdf[ap_].sum() / pdf[lp].sum(), "%", "1 − Σ actual price ÷ Σ list price", sp2)
    sh, hc, hdf = col(r"^health$", r"account", numeric=False)
    if hc:
        add("Revenue in At-Risk accounts", hdf.loc[hdf[hc] == "At Risk", rc].sum() / hdf[rc].sum() if rc else None, "%", "revenue of At Risk accounts ÷ total", sh)
elif model == "B2B2C":
    s, si, df = col(r"sell_in")
    st = col(r"sell_through")[1]; pc = [c for c in (df.columns if df is not None else []) if re.search(r"partner", c, re.I)]
    if si:
        add("Sell-in", df[si].sum(), "#", f"SUM({si})", s)
        if st: add("Sell-through", df[st].sum(), "#", f"SUM({st})", s); add("Sell-through rate", df[st].sum() / df[si].sum(), "%", "sell-through ÷ sell-in", s)
        if pc: g = df.groupby(pc[0])[si].sum(); add("Partner concentration (top partner)", g.max() / g.sum(), "%", "largest partner sell-in ÷ total", s)
        rm = [c for c in df.columns if re.search(r"margin", c, re.I)]
        if rm: add("Partner margin (avg)", df[rm[0]].mean(), "%", f"mean({rm[0]})", s)
    missing("Channel inventory", "partner stock levels"); missing("End-consumer conversion", "end-consumer transactions")
elif model in ("D2C", "B2C"):
    s, ov, df = col(r"order_value|amount|revenue|total")
    if ov:
        add("Revenue", df[ov].sum(), "$", f"SUM({ov})", s); add("Orders", len(df), "#", "count of orders", s); add("AOV", df[ov].mean(), "$", "revenue ÷ orders", s)
        cid = [c for c in df.columns if re.search(r"customer", c, re.I)]
        if cid:
            vc = df[cid[0]].value_counts(); add("Repeat purchase rate", (vc > 1).mean(), "%", "customers with 2+ orders ÷ customers", s)
        rt = [c for c in df.columns if re.search(r"return", c, re.I)]
        if rt:
            add("Return rate", df[rt[0]].mean(), "%", "returned orders ÷ orders", s)
    for m, n in [("Conversion", "sessions or visits"), ("CAC", "marketing spend by period"), ("ROAS", "ad spend and attributed revenue")]:
        missing(m, n)

for k in K:
    p = prev.get(k["name"])
    if p and p.get("value") is not None and k.get("value") is not None:
        k["previous"] = p["value"]; k["change_pct"] = round((k["value"] - p["value"]) / abs(p["value"]) * 100, 1) if p["value"] else None
    if k["name"] in tgt:
        k["target"] = tgt[k["name"]]; k["variance"] = None if k["value"] is None else round(k["value"] - tgt[k["name"]], 4)
    if k["name"] in bm:
        k["benchmark"] = bm[k["name"]]
res = {"framework": model, "asof": str(asof.date()), "kpis": K,
       "supported": sum(k["status"] == "actual" for k in K), "unsupported": [f"{k['name']} (needs {k['needs']})" for k in K if k["status"] == "unsupported"]}
print(json.dumps(res, indent=1, default=str))
if a.out:
    json.dump(res, open(a.out, "w"), indent=1, default=str)
