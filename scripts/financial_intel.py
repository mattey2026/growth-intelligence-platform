#!/usr/bin/env python3
"""
financial_intel.py: Financial Intelligence engine (V7.1). All arithmetic is deterministic (T0); no LLM math.

Input: long-format facts [{entity, period, metric, value, unit, currency, source, source_date, confidence, basis}]
  metric vocabulary: revenue, gross_profit, operating_income, ebitda, d_and_a, net_income, operating_cash_flow, capex,
  free_cash_flow, cash, total_debt, net_debt, current_assets, current_liabilities, accounts_receivable, rd_expense,
  sga_expense, tech_investment, headcount; segments use metric "revenue" with a `segment` (bu:<name> / geo:<name>).
  basis: reported | non_gaap | secondary | derived | estimate (estimates are never promoted to facts).
Optional events: [{entity, date, type: m_and_a|restructuring|investment|divestiture|cost_program|guidance, text, source, source_date}]

Output: metrics per period (value, formula, inputs, provenance, confidence) · missing metrics with the inputs they
need · trends and CAGR · material changes · signals · commercial implications (HYPOTHESIS) · claims typed
FACT / DERIVED / HYPOTHESIS · sensitivity tag · optional persistence (FinancialMetric, FinancialSignal).
--model adapts interpretation: B2B (customer's enterprise spend capacity), B2C (consumer demand, unit economics),
B2B2C (channel margin and partner health).

USAGE: financial_intel.py --facts f.json [--events e.json] [--entity E] [--model B2B] [--public] [--memory-db mem.db] [--out out.json]
"""
import sys
import argparse, json, os, subprocess, hashlib
from collections import defaultdict
ap = argparse.ArgumentParser()
for k in ["facts", "events", "entity", "memory-db", "out"]: ap.add_argument("--" + k)
ap.add_argument("--model", default="B2B"); ap.add_argument("--public", action="store_true")
a = ap.parse_args()
F = json.load(open(a.facts)); EV = json.load(open(a.events)) if a.events else []
ent = a.entity or F[0]["entity"]; F = [f for f in F if f["entity"] == ent]; EV = [e for e in EV if e.get("entity") == ent]
CONF = {"reported": 0.95, "non_gaap": 0.9, "secondary": 0.7, "derived": None, "estimate": 0.4}
base = defaultdict(dict); seg = defaultdict(dict)
for f in F:
    if f.get("value") is None: continue          # an explicit null stays missing
    f["confidence"] = f.get("confidence", CONF.get(f.get("basis", "reported"), 0.8))
    (seg[f["period"]].__setitem__(f["segment"], f) if f.get("segment") else base[f["period"]].__setitem__(f["metric"], f))
periods = sorted(base)
def g(p, m): return base[p].get(m)
M, missing = defaultdict(dict), defaultdict(list)
def put(p, name, val, formula, inputs, unit="ratio"):
    ins = [x for x in inputs if x]
    M[p][name] = {"value": round(val, 4) if val is not None else None, "unit": unit, "formula": formula, "claim_type": "FACT" if formula == "reported" else "DERIVED",
                  "inputs": [{"metric": x["metric"], "value": x["value"], "source": x["source"], "source_date": x.get("source_date"), "basis": x.get("basis")} for x in ins],
                  "confidence": round(min(x["confidence"] for x in ins), 2)}
def need(p, name, req):
    miss = [r for r in req if not g(p, r)]
    if miss: missing[p].append({"metric": name, "needs": miss})
    return not miss
for i, p in enumerate(periods):
    for m, x in base[p].items():
        if x.get("basis") == "estimate": continue
        put(p, m, x["value"], "reported", [x], x.get("unit", "currency"))
    q = periods[i - 1] if i else None
    if q and g(p, "revenue") and g(q, "revenue"):
        put(p, "revenue_growth", g(p, "revenue")["value"] / g(q, "revenue")["value"] - 1, "revenue_t / revenue_t-1 − 1", [g(p, "revenue"), g(q, "revenue")])
    for nm, num, den in [("gross_margin", "gross_profit", "revenue"), ("operating_margin", "operating_income", "revenue"), ("rd_intensity", "rd_expense", "revenue"),
                         ("sga_intensity", "sga_expense", "revenue"), ("capex_intensity", "capex", "revenue"), ("tech_investment_intensity", "tech_investment", "revenue")]:
        if need(p, nm, [num, den]): put(p, nm, g(p, num)["value"] / g(p, den)["value"], f"{num} / {den}", [g(p, num), g(p, den)])
    # EBITDA: reported, or operating income + D&A; never inferred from other ratios
    if g(p, "ebitda"): eb = g(p, "ebitda")["value"]; ebin = [g(p, "ebitda")]
    elif g(p, "operating_income") and g(p, "d_and_a"):
        eb = g(p, "operating_income")["value"] + g(p, "d_and_a")["value"]; ebin = [g(p, "operating_income"), g(p, "d_and_a")]
        put(p, "ebitda", eb, "operating_income + d_and_a", ebin, "currency")
    else:
        eb = None; missing[p].append({"metric": "ebitda", "needs": ["ebitda (reported) or operating_income + d_and_a"]})
    if eb is not None and g(p, "revenue"): put(p, "ebitda_margin", eb / g(p, "revenue")["value"], "ebitda / revenue", ebin + [g(p, "revenue")])
    elif eb is None: missing[p].append({"metric": "ebitda_margin", "needs": ["ebitda"]})
    if not g(p, "free_cash_flow"):
        if need(p, "free_cash_flow", ["operating_cash_flow", "capex"]):
            put(p, "free_cash_flow", g(p, "operating_cash_flow")["value"] - g(p, "capex")["value"], "operating_cash_flow − capex", [g(p, "operating_cash_flow"), g(p, "capex")], "currency")
    fcf = M[p].get("free_cash_flow")
    if fcf and g(p, "revenue"): put(p, "fcf_margin", fcf["value"] / g(p, "revenue")["value"], "free_cash_flow / revenue", [g(p, "free_cash_flow") or g(p, "operating_cash_flow"), g(p, "revenue")])
    if not g(p, "net_debt"):
        if need(p, "net_debt", ["total_debt", "cash"]):
            put(p, "net_debt", g(p, "total_debt")["value"] - g(p, "cash")["value"], "total_debt − cash", [g(p, "total_debt"), g(p, "cash")], "currency")
    nd = M[p].get("net_debt")
    if nd and eb is not None: put(p, "net_debt_to_ebitda", nd["value"] / eb, "net_debt / ebitda", [g(p, "net_debt") or g(p, "total_debt")] + ebin, "x")
    elif nd: missing[p].append({"metric": "net_debt_to_ebitda", "needs": ["ebitda"]})
    if need(p, "working_capital", ["current_assets", "current_liabilities"]):
        put(p, "working_capital", g(p, "current_assets")["value"] - g(p, "current_liabilities")["value"], "current_assets − current_liabilities", [g(p, "current_assets"), g(p, "current_liabilities")], "currency")
    if need(p, "dso", ["accounts_receivable", "revenue"]):
        put(p, "dso", g(p, "accounts_receivable")["value"] / g(p, "revenue")["value"] * 365, "accounts_receivable / revenue × 365", [g(p, "accounts_receivable"), g(p, "revenue")], "days")
    need(p, "capex", ["capex"]); need(p, "cash", ["cash"])
    opex = [g(p, k) for k in ("rd_expense", "sga_expense")]
    if q and all(opex) and all(g(q, k) for k in ("rd_expense", "sga_expense")) and M[p].get("revenue_growth"):
        og = (sum(x["value"] for x in opex) / sum(g(q, k)["value"] for k in ("rd_expense", "sga_expense"))) - 1
        put(p, "opex_growth", og, "(rd+sga)_t / (rd+sga)_t-1 − 1", opex + [g(q, "rd_expense"), g(q, "sga_expense")])
    for sname, x in seg[p].items():
        prevx = seg[q].get(sname) if q else None
        if prevx: put(p, f"segment_growth[{sname}]", x["value"] / prevx["value"] - 1, "segment_t / segment_t-1 − 1", [x, prevx])
# ---- trends, material changes, signals
last, prv = (periods[-1], periods[-2]) if len(periods) > 1 else (periods[-1] if periods else None, None)
v = lambda p, m: M[p].get(m, {}).get("value") if p else None
trends, material, signals = {}, [], []
if len(periods) >= 2 and all(g(p, "revenue") for p in (periods[0], periods[-1])):
    n = len(periods) - 1; trends["revenue_cagr"] = round((g(periods[-1], "revenue")["value"] / g(periods[0], "revenue")["value"]) ** (1 / n) - 1, 4)
for m, thr, kind in [("gross_margin", 0.01, "pp"), ("operating_margin", 0.01, "pp"), ("fcf_margin", 0.02, "pp"), ("revenue_growth", 0.03, "pp"), ("rd_intensity", 0.005, "pp")]:
    a_, b_ = v(last, m), v(prv, m)
    if a_ is not None and b_ is not None:
        d = a_ - b_; trends[m] = {"from": round(b_, 4), "to": round(a_, 4), "change_pp": round(d * 100, 2), "direction": "up" if d > 0 else "down" if d < 0 else "flat"}
        if abs(d) >= thr: material.append({"metric": m, "change_pp": round(d * 100, 2), "periods": [prv, last]})
for m in ["free_cash_flow", "revenue", "operating_income"]:
    a_, b_ = v(last, m), v(prv, m)
    if a_ is not None and b_ not in (None, 0):
        ch = a_ / b_ - 1; trends[m + "_change"] = round(ch, 4)
        if abs(ch) >= (0.2 if m == "free_cash_flow" else 0.05): material.append({"metric": m, "change_pct": round(ch * 100, 1), "periods": [prv, last]})
def sig(kind, text, ev, conf):
    signals.append({"signal_id": "FS-" + hashlib.sha1(f"{ent}{kind}{last}".encode()).hexdigest()[:8], "kind": kind, "text": text, "evidence": ev, "confidence": conf, "period": last, "claim_type": "INFERENCE"})
gm, om = trends.get("gross_margin"), trends.get("operating_margin")
def mtxt(): return "; ".join(f"{n} {x['change_pp']:+.1f}pp ({x['from']:.1%} → {x['to']:.1%})" for n, x in (("gross margin", gm), ("operating margin", om)) if x)
if gm and gm["change_pp"] <= -1 or om and om["change_pp"] <= -1: sig("margin_pressure", "Margin pressure: " + mtxt(), ["gross_margin", "operating_margin"], 0.85)
if gm and gm["change_pp"] >= 1 or om and om["change_pp"] >= 1: sig("margin_expansion", "Margin expansion: " + mtxt(), ["gross_margin", "operating_margin"], 0.85)
rg = v(last, "revenue_growth")
if rg is not None and rg < 0: sig("revenue_decline", f"Revenue declined {rg:.1%}", ["revenue_growth"], 0.9)
if rg is not None and v(prv, "revenue_growth") is not None and rg - v(prv, "revenue_growth") >= 0.03: sig("growth_acceleration", "Revenue growth accelerated ≥3pp", ["revenue_growth"], 0.85)
og = v(last, "opex_growth")
if og is not None and rg is not None:
    if og > rg + 0.01: sig("cost_pressure", f"Opex growth {og:.1%} outpaces revenue growth {rg:.1%}", ["opex_growth", "revenue_growth"], 0.8)
    elif og < rg - 0.01: sig("operating_leverage", f"Opex growth {og:.1%} below revenue growth {rg:.1%}", ["opex_growth", "revenue_growth"], 0.8)
fc = trends.get("free_cash_flow_change")
if fc is not None and fc >= 0.2: sig("cash_generation_improving", f"Free cash flow up {fc:.0%}", ["free_cash_flow"], 0.8)
if fc is not None and fc <= -0.2: sig("cash_generation_weakening", f"Free cash flow down {abs(fc):.0%}", ["free_cash_flow"], 0.8)
ri = trends.get("rd_intensity")
if ri and ri["change_pp"] <= -0.5 or (v(last, "capex_intensity") is not None and v(prv, "capex_intensity") is not None and v(last, "capex_intensity") < v(prv, "capex_intensity") - 0.005):
    sig("investment_reduction", "Investment intensity (R&D or capex) reduced", ["rd_intensity", "capex_intensity"], 0.75)
if (v(last, "tech_investment_intensity") or 0) > (v(prv, "tech_investment_intensity") or 1e9) or any(e["type"] == "investment" for e in EV):
    sig("technology_investment", "Technology investment increasing (metric or announced)", ["tech_investment_intensity"] + [e["text"] for e in EV if e["type"] == "investment"], 0.7)
for e in EV:
    k = {"m_and_a": "m_and_a", "restructuring": "restructuring", "cost_program": "cost_transformation", "divestiture": "divestiture", "guidance": "guidance"}.get(e["type"])
    if k: signals.append({"signal_id": "FS-" + hashlib.sha1(json.dumps(e, sort_keys=True).encode()).hexdigest()[:8], "kind": k, "text": e["text"],
                          "evidence": [{"source": e["source"], "source_date": e.get("source_date"), "date": e.get("date")}], "confidence": 0.9 if e.get("source") else 0.4,
                          "period": last, "claim_type": "FACT" if e.get("source") else "INFERENCE"})
IMP = {"B2B": {"margin_pressure": "Cost-transformation and automation programs become priorities; efficiency offers are timely",
               "cost_pressure": "Opex scrutiny: vendor consolidation and productivity business cases favoured", "revenue_decline": "Discretionary spend at risk; protect renewals, lead with ROI",
               "growth_acceleration": "Capacity to fund growth initiatives; scale and new-market offers", "operating_leverage": "Scaling efficiently; shared-services and platform extensions fit",
               "m_and_a": "Integration, carve-in and harmonization work; stakeholder changes likely", "restructuring": "Transformation and managed-service demand; decision makers may change",
               "technology_investment": "Active technology agenda; modernization and AI programs are fundable", "investment_reduction": "Budget tightening; expect deferrals and procurement pressure",
               "cash_generation_improving": "Healthy funding capacity for multi-year programs", "cash_generation_weakening": "Payment terms and deal phasing sensitivity",
               "cost_transformation": "Explicit cost program: productivity offers aligned to stated targets", "margin_expansion": "Margin gains to protect: efficiency wins valued",
               "divestiture": "Separation / TSA work; account scope may shrink", "guidance": "Management guidance frames next-year priorities"},
       "B2C": {"revenue_decline": "Consumer demand softening: retention and value offers", "margin_pressure": "Unit-economics pressure: pricing, mix, and CAC efficiency",
               "growth_acceleration": "Demand momentum: capacity and acquisition investment"},
       "B2B2C": {"margin_pressure": "Channel margin squeeze: partner programs and pricing at risk", "revenue_decline": "Sell-through slowing: partner inventory and promotions",
                 "growth_acceleration": "Channel expansion opportunity"}}
impl = [{"signal": s["kind"], "implication": IMP.get(a.model, {}).get(s["kind"]) or IMP["B2B"].get(s["kind"], "Review with account team"), "claim_type": "HYPOTHESIS",
         "evidence": [s["signal_id"]], "confidence": round(s["confidence"] * 0.7, 2)} for s in signals]
res = {"entity": ent, "model": a.model, "periods": periods, "metrics": M, "missing": missing, "trends": trends, "material_changes": material, "signals": signals,
       "commercial_implications": impl, "sensitivity": "public_financials" if a.public else "financial_confidential",
       "data_quality": {"secondary_sources": sorted({f["source"] for f in F if f.get("basis") == "secondary"}), "estimates_excluded": [f["metric"] for f in F if f.get("basis") == "estimate"]}}
if a.memory_db:
    objs = []
    for p in periods:
        for m, x in M[p].items():
            src = x["inputs"][0] if x["inputs"] else {}
            objs.append({"obj_type": "FinancialMetric", "account_id": ent, "observed_at": p, "source": src.get("source", "financial_intel.py"), "source_date": src.get("source_date"),
                         "confidence": x["confidence"], "claim_type": x["claim_type"], "data": {"metric": m, "value": x["value"], "unit": x["unit"], "formula": x["formula"], "period": p, "sensitivity": res["sensitivity"]}})
    for s in signals:
        objs.append({"obj_id": s["signal_id"], "obj_type": "FinancialSignal", "account_id": ent, "observed_at": last, "source": "financial_intel.py", "confidence": s["confidence"],
                     "claim_type": s["claim_type"], "data": s})
    f = (a.out or "/tmp/fi") + ".objs.json"; json.dump(objs, open(f, "w"), default=str)
    r = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "memory_graph.py"), a.memory_db, "obj-put", f], capture_output=True, text=True)
    res["memory"] = json.loads(r.stdout) if r.stdout.startswith("{") else {"error": r.stdout or r.stderr}
print(json.dumps(res, indent=1, default=str))
if a.out: json.dump(res, open(a.out, "w"), indent=1, default=str)
