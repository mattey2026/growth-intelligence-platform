#!/usr/bin/env python3
"""
dashboard_builder.py: T0 Dashboard Contract builder (Dashboard Intelligence skill).

bundle (from demo_provider.py or production_provider.py) + persona + role → Dashboard Contract (schemas/dashboard.schema.json).
ALL numbers, deltas, facets, drill paths, anomalies, health dimensions, risks, scenarios and comparisons are computed
here, deterministically. The renderer only displays the contract. Documented rules are in references/metric-definitions.md.

Security: the contract only contains data the role may see (role data classes from the tenant policy). Restricted
data is removed before rendering, not hidden by the UI.

USAGE: dashboard_builder.py --bundle b.json --persona sales_head [--role cro] [--policy tenant-policy.yaml] --out contract.json [--validate]
"""
import sys
import argparse, json, os, statistics, re
from datetime import datetime, date, timedelta
HERE = os.path.dirname(os.path.abspath(__file__)); REF = os.path.join(os.path.dirname(HERE), "references")
ap = argparse.ArgumentParser(); ap.add_argument("--bundle", required=True); ap.add_argument("--persona", default="sales_head"); ap.add_argument("--role", default="cro")
ap.add_argument("--policy"); ap.add_argument("--out", required=True); ap.add_argument("--validate", action="store_true"); a = ap.parse_args()
import yaml
B = json.load(open(a.bundle)); PERS = yaml.safe_load(open(os.path.join(REF, "personas.yaml")))
if a.persona not in PERS: raise SystemExit(json.dumps({"error": f"unknown persona '{a.persona}'", "known": list(PERS)}))
P = PERS[a.persona]
def find_up(rel):
    d = HERE
    for _ in range(6):
        if os.path.exists(os.path.join(d, rel)): return os.path.join(d, rel)
        d = os.path.dirname(d)
pol = yaml.safe_load(open(a.policy or find_up("policy/tenant-policy.example.yaml")))
ROLE = pol["roles"].get(a.role)
DATA = set(ROLE["data"]) if ROLE else {"crm", "public_filings", "web"}     # unknown role → least privilege
CLEAR = set(ROLE.get("clearance", [])) if ROLE else set()
CAN_FIN = "financial_data" in DATA; CAN_MKT = "marketing_data" in DATA
E = B["entity"]; ENAME = E["name"]; ASOF = B["as_of"]; MODE = B["data_mode"]
OPPS = B.get("opportunities") or []
for o in OPPS:
    for k_, d_ in (("category", "Unclassified"), ("driver", "Unclassified"), ("region", "Unassigned"), ("product", "Unassigned"), ("owner", "Unassigned")):
        if not o.get(k_): o[k_] = d_
    for k_ in ("strategic_impact", "growth_value_m", "previous_probability", "created_at", "competitor"): o.setdefault(k_, None)
HAS_GROWTH = bool(OPPS) and all(o["growth_value_m"] is not None for o in OPPS)
HAS_PREVP = bool(OPPS) and all(o["previous_probability"] is not None for o in OPPS)
OSRC = OPPS[0]["source"] if OPPS else "CRM"
# ---------------- formatting (display strings are produced HERE, never in the UI) ----------------
def money(m, d=1): return None if m is None else (f"-${abs(m):,.{d}f}M" if m < 0 else f"${m:,.{d}f}M")
def pct(x, d=1): return None if x is None else f"{x * 100:.{d}f}%"
def spct(x, d=1): return None if x is None else f"{'+' if x > 0 else ''}{x * 100:.{d}f}%"
def spp(x, d=1):
    if x is None: return None
    if round(abs(x) * 100, d) == 0: return f"{0:.{d}f}pp"                   # never show a signed zero ("-0.0pp")
    return f"{'+' if x > 0 else ''}{x * 100:.{d}f}pp"
def smoney(m): return None if m is None else (f"+${m:,.1f}M" if m > 0 else f"-${abs(m):,.1f}M" if m < 0 else "$0.0M")
def direction(d, tol=1e-9): return None if d is None else ("up" if d > tol else "down" if d < -tol else "flat")
RATIO_TOL = 0.0005   # a ratio change smaller than the displayed precision (0.05pp) is "flat", so colour never contradicts the number
def senti(d, good_up=True):
    if d is None or abs(d) < 1e-9: return "neutral"
    return "positive" if (d > 0) == good_up else "negative"
EVID = {}
def ev(eid, source, dt, obs, conf, ct, hist=None, rs=None, ro=None, rd=None, dmode=None):
    EVID[eid] = {"id": eid, "source": source, "date": dt, "observation": obs, "historical_context": hist, "confidence": conf, "claim_type": ct,
                 "related_signals": rs or [], "related_opportunity": ro, "related_decision": rd,
                 "data_mode": dmode or MODE}
    return eid
# ---------------- evidence registry ----------------
# ---- availability: production sources are often partial; everything below is guarded and never invented ----
S = B.get("series") or {}; months = S.get("months", []); rev = S.get("revenue", [])
HAS_S = len(rev) >= 24                                   # TTM and prior-TTM need 24 months
Q = B.get("account_economics") or []; HAS_Q = len(Q) >= 6  # QoQ and YoY need ≥ 6 quarters
EXECS = B.get("executives") or []; OPS_L = B.get("operations") or []
for q in Q:
    ev(f"EV-Q-{q['quarter']}", q["source"], None, f"{q['quarter']}: revenue {money(q['revenue_m'])}, gross profit {money(q['gross_profit_m'])}, cost to serve {money(q['cost_to_serve_m'])}, AR {money(q['accounts_receivable_m'])}", 0.9, "FACT")
if HAS_S: ev("EV-SERIES", S["source"], ASOF, f"Monthly revenue, bookings, pipeline and margin, {months[0]} to {months[-1]}", 0.9, "FACT")

fi = B.get("financial_public")
if fi:
    for p_, ms in fi["metrics"].items():
        for m, x in ms.items():
            for i in x["inputs"]:
                ev(f"EV-PUB-{p_}-{i['metric']}", i["source"], i.get("source_date"), f"{ENAME} {p_} {i['metric'].replace('_', ' ')}: {i['value']:,} ({i.get('basis')})", 0.95 if i.get("basis") != "secondary" else 0.7, "FACT", dmode="public")
    for s in fi["signals"]:
        e0 = s["evidence"][0] if s["evidence"] else {}
        ev(f"EV-{s['signal_id']}", e0.get("source", "financial_intel.py") if isinstance(e0, dict) else "financial_intel.py (computed from cited facts)",
           (e0.get("source_date") if isinstance(e0, dict) else None), s["text"], s["confidence"], s["claim_type"], dmode="public")
thr = B["threads"]; sig_ev = {}
for t in thr:
    for c in t["chronology"]:
        pass
    for e_ in t["evidence"]:
        sid = e_["signal_id"]; txt = next((c["text"] for c in t["chronology"] if c["at"] == e_["at"] and True), "")
        sig_ev[sid] = ev(f"EV-{sid}", e_["source"], e_["at"], next((c["text"] for c in t["chronology"] if c["at"] == e_["at"]), txt), 0.8, "FACT", rs=[t["thread_id"]])
# annotations: evidence supplied by the provider, or a reference to a competitive signal id
for an in B.get("annotations", []):
    if isinstance(an.get("evidence"), dict):
        x = an["evidence"]; an["evidence"] = ev(x["id"], x["source"], x.get("date"), x["observation"], 0.9, "FACT", dmode=x.get("data_mode"))
    elif an.get("signal_id"): an["evidence"] = sig_ev.get(an["signal_id"])
for o in B["opportunities"]:
    ev(f"EV-{o['id']}", o["source"], o.get("created_at"), f"{o['name']}: {o['stage']}, {money(o['value_m'])}, probability {pct(o['probability'], 0)}" + (f" (was {pct(o['previous_probability'], 0)})" if o['previous_probability'] is not None else ""), 0.85, "FACT", ro=o["id"])
for x in EXECS:
    ev(f"EV-{x['id']}", x["source"], x["last_interaction"], f"{x['name']} ({x['role']}): relationship {x['strength']}, trend {x['trend']}, last interaction {x['last_interaction']}", 0.8, "FACT")
mk = B.get("marketing") or {}
MS_EV = {}
if CAN_MKT and mk:
    for u, v in mk.get("units", {}).items():
        for sid in (v.get("buying_intent", {}).get("evidence", []) + ((v.get("executive_engagement") or {}).get("evidence", []))):
            MS_EV[sid] = ev(f"EV-{sid}", "DEMO DATA — NOT REAL CUSTOMER DATA (marketing automation)" if MODE == "demo" else "marketing automation", None, f"Marketing signal {sid} ({u})", 0.85, "FACT")
for r in B.get("relationship_signals", []):
    ev(f"EV-{r['signal_id']}", r["source"], r["observed_at"], f"{r['kind'].replace('_', ' ')}: {r['stakeholder']}", 0.8, "FACT")
for o in B.get("operations", []):
    ev(f"EV-OPS-{o['id']}", o["source"], ASOF, f"{o['label']}: {o['value']} (previous {o['previous']})", 0.85, "FACT")
for d in B.get("decisions", []):
    ev(f"EV-{d['id']}", d["source"], ASOF, d["question"], d["confidence"], "RECOMMENDATION", rd=d["id"])
for e_ in B.get("market_events", []):
    ev(f"EV-MKT-{e_['type']}", e_["source"], e_.get("source_date"), e_["text"], 0.95, "FACT", dmode="public" if e_.get("public", True) else MODE)
# ---------------- core computations ----------------

threads_active = [t for t in thr if t["status"] == "active" and t["thread_type"] in ("displacement_risk", "competitive_pursuit")]
threat_by_comp = {}
for t in threads_active:
    if t["competitor_id"] not in threat_by_comp or {"High": 3, "Medium": 2, "Low": 1}[t["risk_level"]] > {"High": 3, "Medium": 2, "Low": 1}[threat_by_comp[t["competitor_id"]]["risk_level"]]:
        threat_by_comp[t["competitor_id"]] = t
prev_date = B["delta_snapshots"]["previous"]["as_of"] if B.get("delta_snapshots") else None
def contested(o, when=None):
    t = threat_by_comp.get(o.get("competitor"))
    return bool(t and t["risk_level"] in ("High", "Medium") and (when is None or t["first_signal"] <= when))
def opp_facets(o):
    return {"competitor": [o["competitor"]] if o.get("competitor") else ["None"], "driver": [o["driver"]], "category": [o["category"]], "region": [o["region"]],
            "product": [o["product"]], "domain": ["pipeline"], "stakeholder": [x["id"] for x in EXECS if o["id"] in x.get("opportunities", [])], "opportunity": [o["id"]]}
for o in OPPS: o["_f"] = opp_facets(o)
FACET_DIMS = ["competitor", "driver", "category", "region", "product", "domain", "stakeholder"]
def agg(fn, pred=lambda o: True):
    vals = [fn(o) for o in OPPS if pred(o)]
    return round(sum(v for v in vals if v is not None), 4)
def by_facet(fn, fmt, prev_fn=None):
    out = {}
    for dim in ["competitor", "driver", "category", "region", "product", "stakeholder"]:
        vals = sorted({v for o in OPPS for v in o["_f"][dim]})
        out[dim] = {val: {"value": agg(fn, lambda o, d=dim, v=val: v in o["_f"][d]), "display": fmt(agg(fn, lambda o, d=dim, v=val: v in o["_f"][d]))} for val in vals}
    return out
ttm, pttm = (sum(rev[-12:]), sum(rev[-24:-12])) if HAS_S else (None, None)
q_rev = [q["revenue_m"] for q in Q]
yoy_q, yoy_q_prev = (q_rev[-1] / q_rev[-5] - 1, q_rev[-2] / q_rev[-6] - 1) if HAS_Q else (None, None)
gm = [q["gross_profit_m"] / q["revenue_m"] for q in Q]
pipe = agg(lambda o: o["value_m"])
pipe_prev = B["delta_snapshots"]["previous"]["domains"].get("commercial_state", {}).get("pipeline_total_m", {}).get("value") if B.get("delta_snapshots") else None
fc = agg(lambda o: o["value_m"] * o["probability"]); fc_prev = agg(lambda o: o["value_m"] * o["previous_probability"]) if HAS_PREVP else None
gp = agg(lambda o: o["growth_value_m"]) if HAS_GROWTH else None
gp_prev = agg(lambda o: o["growth_value_m"], lambda o: not prev_date or (o.get("created_at") or "0") <= prev_date) if HAS_GROWTH and prev_date else None
ov = agg(lambda o: o["value_m"], lambda o: o["category"] != "Renewal")
ov_prev = agg(lambda o: o["value_m"], lambda o: o["category"] != "Renewal" and (o.get("created_at") or "9") <= prev_date) if prev_date and all(o.get("created_at") for o in OPPS) else None
rx = agg(lambda o: o["value_m"] * (1 - o["probability"]), lambda o: contested(o))
rx_prev = agg(lambda o: o["value_m"] * (1 - o["previous_probability"]), lambda o: contested(o, prev_date)) if HAS_PREVP and prev_date else None
cx = agg(lambda o: o["value_m"], lambda o: contested(o)) / pipe if pipe else None
cx_prev = (agg(lambda o: o["value_m"], lambda o: contested(o, prev_date)) / pipe_prev) if pipe_prev and prev_date else None
pipe_series = S.get("pipeline", [])
dso = [q["accounts_receivable_m"] / q["revenue_m"] * 91 for q in Q]
def D_(a, b, f): return (round(a - b, 4), f(a - b)) if a is not None and b is not None else (None, None)
def metric(id_, label, value, display, prev, prev_display, delta, delta_display, good_up, conf, source, evidence, drill, trend=None, unit=None, facet=None, note=None, restricted=False):
    if delta_display and re.fullmatch(r"[+-]?\$?0(\.0+)?(pp|%|M)?", delta_display.replace("$", "")): delta = 0.0   # displayed zero → flat, neutral
    return {"id": id_, "label": label, "value": value, "unit": unit, "display": display, "previous_value": prev, "previous_display": prev_display, "delta": delta,
            "delta_display": delta_display, "direction": direction(delta), "sentiment": senti(delta, good_up), "trend": trend or [], "confidence": conf, "source": source,
            "timestamp": ASOF, "evidence": evidence, "drill_down_target": drill, "claim_type": "DERIVED", "by_facet": facet or {}, "note": note, "data_mode": MODE}
src_bill = S.get("source", "billing")
def na(id_, needs):
    return {"id": id_, "label": LBLS[id_], "value": None, "unit": None, "display": "Not available", "previous_value": None, "previous_display": None, "delta": None, "delta_display": None,
            "direction": None, "sentiment": "neutral", "trend": [], "confidence": None, "source": None, "timestamp": ASOF, "evidence": [], "drill_down_target": None, "claim_type": None,
            "by_facet": {}, "note": f"Not available: needs {needs}", "data_mode": MODE, "available": False}
LBLS = {'revenue': 'Revenue (TTM)', 'revenue_growth': 'Growth (qtr YoY)', 'pipeline': 'Pipeline', 'forecast': 'Forecast (weighted)', 'margin': 'Account margin', 'growth_potential': 'Growth potential', 'opportunity_value': 'New opportunities', 'risk_exposure': 'Value at risk', 'competitive_exposure': 'Competitive exposure'}
HAS_CAT = bool(OPPS) and all(o.get("category") not in (None, "Unclassified") for o in OPPS)   # renewal vs new needs categories
HAS_COMP = bool(thr)   # without competitive signals exposure is UNKNOWN, not zero
KPI = {}
KPI["revenue"] = metric("revenue", "Revenue (TTM)", round(ttm, 2), money(ttm), round(pttm, 2), money(pttm), round(ttm / pttm - 1, 4), spct(ttm / pttm - 1), True, 0.9, src_bill, ["EV-SERIES"] + [f"EV-Q-{q['quarter']}" for q in Q[-4:]], "D-revenue",
                   [round(sum(rev[i - 11:i + 1]), 2) for i in range(len(rev) - 13, len(rev))], "USD m", note="Not split by competitor or driver (billing data has no opportunity link)") if (HAS_S) else na("revenue", "24 months of billing history")
KPI["revenue_growth"] = metric("revenue_growth", "Growth (qtr YoY)", round(yoy_q, 4), spct(yoy_q), round(yoy_q_prev, 4), spct(yoy_q_prev), round(yoy_q - yoy_q_prev, 4), spp(yoy_q - yoy_q_prev), True, 0.9, src_bill,
                   [f"EV-Q-{Q[-1]['quarter']}", f"EV-Q-{Q[-5]['quarter']}"], "D-revenue_growth", [round(q_rev[i] / q_rev[i - 4] - 1, 4) for i in range(4, len(q_rev))], "ratio") if (HAS_Q) else na("revenue_growth", "6 quarters of account revenue")
KPI["pipeline"] = metric("pipeline", "Pipeline", pipe, money(pipe), pipe_prev, money(pipe_prev), round(pipe - pipe_prev, 2) if pipe_prev else None, smoney(pipe - pipe_prev) if pipe_prev else None, True, 0.85,
                   OSRC, [f"EV-{o['id']}" for o in OPPS], "D-pipeline", pipe_series[-12:], "USD m", by_facet(lambda o: o["value_m"], money)) if (OPPS) else na("pipeline", "open opportunities")
KPI["forecast"] = metric("forecast", "Forecast (weighted)", fc, money(fc), fc_prev, money(fc_prev), *((round(fc - fc_prev, 2), smoney(fc - fc_prev)) if fc_prev is not None else (None, None)), True, 0.7, OSRC, [f"EV-{o['id']}" for o in OPPS],
                   "D-forecast", None, "USD m", by_facet(lambda o: o["value_m"] * o["probability"], money), note="Σ value × probability (CRM probabilities)") if (OPPS) else na("forecast", "open opportunities with probabilities")
KPI["margin"] = metric("margin", "Account margin", round(gm[-1], 4), pct(gm[-1]), round(gm[-2], 4), pct(gm[-2]), round(gm[-1] - gm[-2], 4), spp(gm[-1] - gm[-2]), True, 0.9, Q[-1]["source"],
                   [f"EV-Q-{Q[-1]['quarter']}", f"EV-Q-{Q[-2]['quarter']}"], "D-margin", [round(x, 4) for x in gm], "ratio") if (HAS_Q and CAN_FIN) else na("margin", "quarterly account P&L (and financial_data access)")
KPI["growth_potential"] = metric("growth_potential", "Growth potential", gp, money(gp), gp_prev, money(gp_prev), *((round(gp - gp_prev, 2), smoney(gp - gp_prev)) if gp_prev is not None else (None, None)), True, 0.7, OSRC, [f"EV-{o['id']}" for o in OPPS],
                   "D-growth_potential", None, "USD m", by_facet(lambda o: o["growth_value_m"], money), note="Incremental growth: renewals count only their uplift") if (HAS_GROWTH) else na("growth_potential", "incremental growth value per opportunity")
KPI["opportunity_value"] = metric("opportunity_value", "New opportunities", ov, money(ov), ov_prev, money(ov_prev), *((round(ov - ov_prev, 2), smoney(ov - ov_prev)) if ov_prev is not None else (None, None)), True, 0.8, OSRC,
                   [f"EV-{o['id']}" for o in OPPS if o["category"] != "Renewal"], "D-opportunity_value", None, "USD m", by_facet(lambda o: o["value_m"] if o["category"] != "Renewal" else 0, money)) if (OPPS and HAS_CAT) else na("opportunity_value", "opportunity categories (to separate renewals from new business)")
KPI["risk_exposure"] = metric("risk_exposure", "Value at risk", rx, money(rx), rx_prev, money(rx_prev), *((round(rx - rx_prev, 2), smoney(rx - rx_prev)) if rx_prev is not None else (None, None)), False, 0.65, "dashboard_builder.py (T0 rule)",
                   [sig_ev.get(e_["signal_id"]) for t in threat_by_comp.values() for e_ in t["evidence"]][:8], "D-risk_exposure", None, "USD m",
                   by_facet(lambda o: o["value_m"] * (1 - o["probability"]) if contested(o) else 0, money), note="Σ value × (1 − probability) for opportunities contested by an active Medium/High threat thread") if (OPPS and HAS_COMP) else na("risk_exposure", "competitive signals (Competitive Thread memory) and open opportunities")
KPI["competitive_exposure"] = metric("competitive_exposure", "Competitive exposure", round(cx, 4), pct(cx, 0), round(cx_prev, 4) if cx_prev is not None else None, pct(cx_prev, 0),
                   round(cx - cx_prev, 4) if cx_prev is not None else None, spp(cx - cx_prev) if cx_prev is not None else None, False, 0.7, "dashboard_builder.py (T0 rule)",
                   [f"EV-{o['id']}" for o in OPPS if contested(o)], "D-competitive_exposure", None, "ratio", note="Share of pipeline value contested by an active Medium/High threat thread") if (OPPS and pipe and HAS_COMP) else na("competitive_exposure", "competitive signals (Competitive Thread memory) and open opportunities")
restricted = []
if not CAN_FIN:
    KPI.pop("margin"); restricted.append({"item": "Account gross margin and account economics", "needs": "financial_data"})
metrics = [KPI[k] for k in P["kpis"] if k in KPI]
# ---------------- trends + anomaly detection ----------------
def pts(ms, vs): return [{"t": m_, "v": v_} for m_, v_ in zip(ms, vs)]
if HAS_S:
    yoy_m = [round(rev[i] / rev[i - 12] - 1, 4) for i in range(12, 24)]
    trends = [
     {"id": "revenue", "label": "Revenue", "unit": "USD m", "format": "money", "series": [{"name": "actual", "points": pts(months, rev)}, {"name": "target", "points": pts(months, S["target"])},
       {"name": "previous_year", "points": pts(months[12:], rev[:12])}, {"name": "forecast", "points": pts(S["forecast"]["months"], S["forecast"]["values"])}], "evidence": ["EV-SERIES"]},
     {"id": "growth", "label": "Growth (YoY, monthly)", "unit": "ratio", "format": "pct", "series": [{"name": "actual", "points": pts(months[12:], yoy_m)}], "evidence": ["EV-SERIES"]},
     {"id": "pipeline", "label": "Pipeline", "unit": "USD m", "format": "money", "series": [{"name": "actual", "points": pts(months, pipe_series)}, {"name": "previous_year", "points": pts(months[12:], pipe_series[:12])}], "evidence": ["EV-SERIES"]},
     {"id": "bookings", "label": "Bookings", "unit": "USD m", "format": "money", "series": [{"name": "actual", "points": pts(months, S["bookings"])}, {"name": "previous_year", "points": pts(months[12:], S["bookings"][:12])}], "evidence": ["EV-SERIES"]},
     {"id": "forecast", "label": "Forecast", "unit": "USD m", "format": "money", "series": [{"name": "actual", "points": pts(months[-6:], rev[-6:])}, {"name": "forecast", "points": pts(S["forecast"]["months"], S["forecast"]["values"])},
       {"name": "prior_forecast", "points": pts(S["prior_forecast"]["months"], S["prior_forecast"]["values"])}], "evidence": ["EV-SERIES"]}]
    if CAN_FIN: trends.insert(4, {"id": "margin", "label": "Account margin", "unit": "ratio", "format": "pct", "series": [{"name": "actual", "points": pts(months, S["margin"])}], "evidence": ["EV-SERIES"]})
else:
    trends = []
annots = [dict(x, t=x["t"]) for x in B.get("annotations", [])]
for t_ in trends: t_["annotations"] = [x for x in annots if any(p_["t"] == x["t"] for s_ in t_["series"] for p_ in s_["points"])]
# Trend-adjusted anomaly rule: project the trailing 6 months with a least-squares line; flag a month whose deviation
# from that projection is ≥ 7% AND ≥ 3× the trailing residual scale (floored at 1% of the mean). Plain z-scores against a
# flat mean mislabel ordinary growth as anomalies in smooth series, so they are not used.
anomalies = []
for i in range(6, len(rev) if HAS_S else 0):
    w = rev[i - 6:i]; xs = range(6); mx, my = 2.5, statistics.mean(w)
    b1 = sum((x - mx) * (y - my) for x, y in zip(xs, w)) / sum((x - mx) ** 2 for x in xs); b0 = my - b1 * mx
    expected = b0 + b1 * 6
    scale = max(statistics.pstdev([y - (b0 + b1 * x) for x, y in zip(xs, w)]), 0.01 * my)
    dev = rev[i] - expected
    if abs(dev) / expected >= 0.07 and abs(dev) >= 3 * scale:
        anomalies.append({"t": months[i], "value": rev[i], "expected": round(expected, 3), "dev_pct": round(dev / expected, 4), "z": round(dev / scale, 1)})
# ---------------- insights ----------------
insights = []
for an in anomalies:
    insights.append({"id": f"INS-ANOM-{an['t']}", "label": f"Revenue anomaly in {an['t']}", "text": f"Revenue of {money(an['value'], 2)} in {an['t']} was {abs(an['dev_pct']) * 100:.0f}% {'below' if an['dev_pct'] < 0 else 'above'} the {money(an['expected'], 2)} expected from the prior six-month trend.",
                     "claim_type": "FACT", "confidence": 0.9, "evidence": ["EV-SERIES"] + [x["evidence"] for x in B.get("annotations", []) if x["t"] == an["t"] and x.get("evidence")], "severity": "warning", "anomaly": True, "facets": {"domain": ["financial"]}})
slope = gm[-1] - gm[-5] if HAS_Q else None
insights.append(None if not (CAN_FIN and HAS_Q) else {"id": "INS-MARGIN-TREND", "label": "Account margin trend", "text": f"Account gross margin moved from {pct(gm[-5])} to {pct(gm[-1])} over four quarters ({spp(slope)}).", "claim_type": "FACT",
                 "confidence": 0.9, "evidence": [f"EV-Q-{Q[-5]['quarter']}", f"EV-Q-{Q[-1]['quarter']}"], "severity": "warning" if slope < -0.005 else "info", "anomaly": False, "facets": {"domain": ["financial"]}} if CAN_FIN and HAS_Q else None)
insights = [x for x in insights if x]
for p_ in (B.get("correlation") or {}).get("patterns", []):
    if p_["status"] == "not_detected": continue
    insights.append({"id": f"INS-{p_['pattern_id']}", "label": p_["name"].replace("_", " ").capitalize(), "text": p_["text"] + ". " + (p_.get("caution") or ""), "claim_type": "HYPOTHESIS",
                     "confidence": p_["confidence"], "evidence": [sig_ev.get(x) or MS_EV.get(x) or (f"EV-{x}" if f"EV-{x}" in EVID else None) for x in p_["supporting_evidence"] if isinstance(x, str)] and
                     [e_ for e_ in [sig_ev.get(x) or MS_EV.get(x) or (f"EV-{x}" if f"EV-{x}" in EVID else None) for x in p_["supporting_evidence"] if isinstance(x, str)] if e_] or ["EV-SERIES"],
                     "severity": "risk" if p_["pattern_id"] in ("P3", "P4") else "opportunity", "anomaly": False, "missing_evidence": p_["missing_evidence"],
                     "facets": {"domain": ["competitive"] if p_["pattern_id"] == "P4" else ["marketing"] if p_["pattern_id"] == "P1" else ["financial"], **({"competitor": sorted({t["competitor_id"] for t in threads_active if t["risk_level"] == "High"})} if p_["pattern_id"] == "P4" else {})}})
# ---------------- opportunities, drivers ----------------
CATS = ["New Business", "Expansion", "Cross-sell", "Displacement", "Renewal", "Transformation"]
def opp_obj(o):
    t = threat_by_comp.get(o.get("competitor"))
    return {"id": o["id"], "label": o["name"], "category": o["category"], "value": o["value_m"], "unit": "USD m", "display": money(o["value_m"]), "probability": o["probability"],
            "previous_value": o["previous_probability"], "probability_display": pct(o["probability"], 0), "previous_display": pct(o["previous_probability"], 0),
            **(lambda dp: {"delta": dp, "delta_display": spp(dp, 0) if dp is not None else None, "direction": direction(dp)})(round(o["probability"] - o["previous_probability"], 2) if o["previous_probability"] is not None else None),
            "weighted_display": money(o["value_m"] * o["probability"]), "strategic_impact": o["strategic_impact"], "stage": o["stage"], "close_date": o["close_date"], "owner": o["owner"],
            "competitor": o.get("competitor"), "region": o["region"], "product": o["product"], "driver": o["driver"], "growth_value_display": money(o["growth_value_m"]) if o["growth_value_m"] is not None else "not provided",
            "competitive_context": (f"{t['competitor_id']} thread {t['momentum']}, risk {t['risk_level']}" if t else ("No active competitor" if not o.get("competitor") else f"{o['competitor']}: no active threat thread")),
            "stakeholders": [x["id"] for x in EXECS if o["id"] in x["opportunities"]], "confidence": round(min(0.9, 0.5 + 0.4 * o["probability"]), 2), "source": o["source"],
            "timestamp": o.get("created_at"), "evidence": [f"EV-{o['id']}"] + ([sig_ev[e_["signal_id"]] for e_ in t["evidence"] if e_["signal_id"] in sig_ev][:3] if t else []),
            "drill_down_target": f"D-opp-{o['id']}", "claim_type": "FACT", "facets": o["_f"], "data_mode": MODE}
opps = [opp_obj(o) for o in OPPS]
DRV = ["New Business", "Expansion", "Cross-Sell", "Pricing", "Market Growth"]
drivers = ({"id": "growth_potential", "label": "Growth potential", "available": False, "value": None, "display": "Not available",
            "needs": "incremental growth value per opportunity (not in the source data)", "children": []} if not HAS_GROWTH else None) or {"id": "growth_potential", "label": "Growth potential", "value": gp, "display": money(gp), "drill_down_target": "D-growth_potential",
           "children": [{"id": f"drv-{d.lower().replace(' ', '-')}", "label": d, "value": agg(lambda o: o["growth_value_m"], lambda o, d=d: o["driver"] == d),
                         "display": money(agg(lambda o: o["growth_value_m"], lambda o, d=d: o["driver"] == d)), "facet": {"driver": d}, "drill_down_target": f"D-drv-{d}",
                         "count": sum(1 for o in OPPS if o["driver"] == d)} for d in DRV]}
# ---------------- competition ----------------
comps = sorted({t["competitor_id"] for t in thr} | {o["competitor"] for o in OPPS if o.get("competitor")})
landscape = []
for c in comps:
    ct = [t for t in thr if t["competitor_id"] == c]; ov_ = [o for o in OPPS if o.get("competitor") == c]
    recent = sum(1 for t in ct for x in t["chronology"] if (datetime.fromisoformat(ASOF) - datetime.fromisoformat(x["at"])).days <= 90)
    th_ = threat_by_comp.get(c); op_ = [t for t in ct if t["thread_type"] == "displacement_opportunity" and t["status"] == "active"]
    landscape.append({"id": f"comp-{c}", "label": c, "footprint": len({s for o in ov_ for s in o["_f"]["stakeholder"]}), "overlap_opportunities": len(ov_), "overlap_value": round(sum(o["value_m"] for o in ov_), 2),
                      "overlap_display": money(sum(o["value_m"] for o in ov_)), "activity_90d": recent, "threat": th_["risk_level"] if th_ else "None", "momentum": th_["momentum"].split(" (")[0] if th_ else "—", "momentum_detail": th_["momentum"] if th_ else None,
                      "opportunity_momentum": op_[0]["momentum"].split(" (")[0] if op_ else None,
                      "displacement_opportunity": op_[0]["opportunity_level"] if op_ else None, "threads": len(ct), "facets": {"competitor": [c], "domain": ["competitive"]},
                      "drill_down_target": f"D-comp-{c}", "evidence": [sig_ev[e_["signal_id"]] for t in ct for e_ in t["evidence"] if e_["signal_id"] in sig_ev][:5], "confidence": max([t["confidence"] for t in ct] or [0.3])})
KL = {"competitor_mention": "Mention", "competitor_exec_meeting": "Executive meeting", "rfp_participation": "RFP", "pricing_undercut": "Pricing pressure", "competitor_pilot": "Pilot offer",
      "champion_weakening": "Champion weakening", "competitor_delivery_issue": "Delivery issue", "competitor_exit": "Competitor exit", "customer_positive_on_us": "Customer praised us",
      "our_win_against": "We won", "competitor_shortlisted": "Shortlisted", "competitor_hire_into_account": "Insider hire", "competitor_contract_award": "Contract award", "competitor_price_rise": "Price rise", "competitor_reference": "Reference"}
ACTIONS = []
def action(id_, label, reason, evidence, owner, priority, due, impact, catalog, facets, source_obj):
    approval = catalog not in ("notify.owner_internal", "memory.write_summary", "email.draft")
    ACTIONS.append({"id": id_, "label": label, "reason": reason, "evidence": [e_ for e_ in evidence if e_], "owner": owner, "priority": priority, "due": due, "expected_impact": impact,
                    "catalog_action": catalog, "approval_required": approval, "status": "proposed", "governance": "Executed only through the Action Center: policy gate, then human approval" if approval else "Low-risk internal action; still logged by the Action Center",
                    "claim_type": "RECOMMENDATION", "confidence": None, "source": source_obj, "timestamp": ASOF, "facets": facets, "drill_down_target": None, "data_mode": MODE})
    return id_
def due_in(days): return (datetime.fromisoformat(ASOF) + timedelta(days=days)).date().isoformat()
threads = []
for t in thr:
    lo = [o for o in OPPS if o["id"] in t["opportunities"] or (o.get("competitor") == t["competitor_id"] and t["thread_type"] != "displacement_opportunity")]
    aid = None
    if t["recommended_actions"] and t["status"] == "active":
        ra = t["recommended_actions"][0]; val = sum(o["value_m"] for o in lo)
        aid = action(f"ACT-{t['thread_id']}", ra["action"] + f" ({t['competitor_id']})", ra["why"], [sig_ev.get(e_["signal_id"]) for e_ in t["evidence"]][:4], lo[0]["owner"] if lo else "Account Director",
                     "P1" if t["risk_level"] == "High" else "P2", due_in(7 if t["risk_level"] == "High" else 21), f"Protects {money(val)} of contested pipeline" if val and t["thread_type"] != "displacement_opportunity" else f"Opens a displacement pursuit" ,
                     "crm.create_task", {"competitor": [t["competitor_id"]], "domain": ["competitive"]}, "competitive_threads.py")
    fac = {"competitor": [t["competitor_id"]], "domain": ["competitive"]}
    for o in lo:
        for dim in ("driver", "category", "region", "product", "stakeholder"): fac.setdefault(dim, []); fac[dim] = sorted(set(fac[dim]) | set(o["_f"][dim]))
    pne = t.get("predicted_next_event")
    opp_t = t["thread_type"] == "displacement_opportunity"
    msent = "neutral" if t["momentum"] in ("steady", "resolved") else ("positive" if (t["momentum"].startswith("accel") == opp_t) else "negative")
    threads.append({"id": t["thread_id"], "label": f"{t['competitor_id']}: {t['thread_type'].replace('_', ' ')} at {ENAME}", "competitor": t["competitor_id"], "thread_type": t["thread_type"], "status": t["status"],
                    "momentum": t["momentum"].split(" (")[0], "momentum_detail": t["momentum"], "momentum_sentiment": msent,
                    "signal_count": t["signal_count"], "velocity": t["signal_velocity"], "velocity_display": f"{t['signal_velocity']:.1f} / 30 days", "confidence": t["confidence"],
                    "risk": t["risk_level"], "opportunity_level": t["opportunity_level"], "first_signal": t["first_signal"], "latest_signal": t["latest_signal"],
                    "chronology": [{"t": c["at"], "kind": c["kind"], "label": KL.get(c["kind"], c["kind"]), "text": c["text"], "polarity": c["polarity"],
                                    "evidence": sig_ev.get(next((e_["signal_id"] for e_ in t["evidence"] if e_["at"] == c["at"]), ""), None)} for c in t["chronology"]],
                    "counter_evidence": t["counter_evidence"], "predicted_next_event": pne, "recommended_action_id": aid, "outcome": t.get("outcome"),
                    "opportunities": [o["id"] for o in lo], "evidence": [sig_ev[e_["signal_id"]] for e_ in t["evidence"] if e_["signal_id"] in sig_ev], "source": "competitive_threads.py",
                    "timestamp": t["latest_signal"], "claim_type": "INFERENCE", "facets": fac, "drill_down_target": f"D-thread-{t['thread_id']}", "data_mode": MODE})
# ---------------- risks ----------------
LV = {"High": 0.75, "Medium": 0.5, "Low": 0.25}
risks = []
def risk(id_, label, cat, lik, imp, imp_disp, owner, trend, mit, conf, evid, facets, ct="INFERENCE"):
    risks.append({"id": id_, "label": label, "category": cat, "likelihood": round(min(0.95, lik), 2), "impact": round(min(1.0, imp), 2), "impact_display": imp_disp, "owner": owner,
                  "trend": trend, "mitigation": mit, "confidence": conf, "evidence": [e_ for e_ in evid if e_], "facets": facets, "claim_type": ct, "source": "dashboard_builder.py (T0 rules)",
                  "timestamp": ASOF, "drill_down_target": f"D-risk-{id_}", "data_mode": MODE})
for t in threads_active:
    lo = [o for o in OPPS if o.get("competitor") == t["competitor_id"]]; val = sum(o["value_m"] for o in lo)
    if t["risk_level"] == "Low": continue
    risk(f"R-{t['thread_id']}", f"{t['competitor_id']} gaining ground ({t['thread_type'].replace('_', ' ')})", "Competitive", LV[t["risk_level"]] + (0.1 if t["momentum"] == "accelerating" else 0),
         val / max(o["value_m"] for o in OPPS), f"{money(val)} contested", lo[0]["owner"] if lo else "Account Director", "rising" if t["momentum"] == "accelerating" else "stable",
         t["recommended_actions"][0]["action"] if t["recommended_actions"] else "Monitor the thread", t["confidence"], [sig_ev.get(e_["signal_id"]) for e_ in t["evidence"]][:4],
         {"competitor": [t["competitor_id"]], "domain": ["competitive"], **{d: sorted({v for o in lo for v in o["_f"][d]}) for d in ("driver", "category", "region")}})
dp = [(o, o["previous_probability"] - o["probability"]) for o in OPPS if o.get("previous_probability") is not None and o["previous_probability"] - o["probability"] >= 0.05]
for o, d in dp:
    risk(f"R-PROB-{o['id']}", f"{o['name']}: probability fell {abs(d) * 100:.0f}pp", "Pipeline", 0.6, o["value_m"] * d / 5, f"{money(o['value_m'] * d)} weighted", o["owner"], "rising",
         "Review the close plan and the decision process", 0.8, [f"EV-{o['id']}"], o["_f"], "FACT")
if B.get("delta_snapshots"):
    cs_ = B["delta_snapshots"]
    for k, x in cs_["current"]["domains"]["commercial_state"].items():
        if k.endswith(":close_date"):
            pv = cs_["previous"]["domains"]["commercial_state"].get(k, {}).get("value")
            if pv and pv != x["value"]:
                o = next(o for o in OPPS if o["id"] == k.split(":")[0])
                risk(f"R-SLIP-{o['id']}", f"{o['name']} slipped {pv} → {x['value']}", "Pipeline", 0.55, o["value_m"] / 25, money(o["value_m"]), o["owner"], "rising", "Confirm the decision date with the sponsor", 0.8, [f"EV-{o['id']}"], o["_f"], "FACT")
if CAN_FIN and HAS_Q:
    if gm[-1] < gm[-5] - 0.005: risk("R-FIN-MARGIN", "Account margin compression", "Financial", 0.7, 0.45, f"{spp(gm[-1] - gm[-5])} over 4 quarters", "Delivery Finance", "rising",
                                     "Review cost to serve and rate card at renewal", 0.85, [f"EV-Q-{Q[-1]['quarter']}", f"EV-Q-{Q[-5]['quarter']}"], {"domain": ["financial"]}, "FACT")
    if dso[-1] > dso[-5] + 3: risk("R-FIN-DSO", f"Collections slowing: DSO {dso[-5]:.0f} → {dso[-1]:.0f} days", "Financial", 0.55, 0.35, f"{dso[-1] - dso[-5]:+.0f} days", "Collections", "rising",
                                   "Escalate aged invoices with the customer's AP team", 0.85, [f"EV-Q-{Q[-1]['quarter']}"], {"domain": ["financial"]}, "FACT")
ops = {o["id"]: o for o in OPS_L}
if "csat" in ops and "open_escalations" in ops and ops["csat"]["value"] < ops["csat"]["previous"]:
    risk("R-CUST-CSAT", "Customer satisfaction declining with escalations rising", "Customer", 0.5, 0.5, f"CSAT {ops['csat']['previous']} → {ops['csat']['value']}; escalations {ops['open_escalations']['previous']} → {ops['open_escalations']['value']}",
         "Service Delivery Lead", "rising", "Run an escalation review with the CIO office", 0.8, ["EV-OPS-csat", "EV-OPS-open_escalations"], {"domain": ["customer"]}, "FACT")
if "sla_attainment" in ops and ops["sla_attainment"]["value"] < ops["sla_attainment"]["previous"]:
    risk("R-OPS-SLA", f"SLA attainment slipped to {pct(ops['sla_attainment']['value'])}", "Operational", 0.45, 0.4, spp(ops["sla_attainment"]["value"] - ops["sla_attainment"]["previous"]), "Service Delivery Lead", "rising",
         "Add capacity to the backlog queue", 0.85, ["EV-OPS-sla_attainment", "EV-OPS-backlog"], {"domain": ["operational"]}, "FACT")
for r in B.get("relationship_signals", []):
    if r["kind"] == "champion_weakening":
        x = next((x for x in EXECS if x["id"] == r["stakeholder"]), None)
        if not x: continue
        risk(f"R-REL-{x['id']}", f"Champion weakening: {x['role']}", "Customer", 0.6, 0.6, f"Linked to {len(x['opportunities'])} opportunities", "Account Director", "rising",
             "Build a second champion; executive sponsor call", 0.8, [f"EV-{r['signal_id']}", f"EV-{x['id']}"], {"stakeholder": [x["id"]], "domain": ["relationship"], "competitor": sorted({t["competitor_id"] for t in thr if x["id"] in t.get("stakeholders", [])})}, "FACT")
for e_ in B.get("market_events", []):
    if e_["type"] == "m_and_a":
        risk("R-MKT-MA", "Customer acquisition integration may shift priorities", "Market", 0.3, 0.3, "Priority and stakeholder changes", "Account Director", "stable",
             "Map integration leaders; position integration services", 0.4, [f"EV-MKT-{e_['type']}"], {"domain": ["market"]}, "HYPOTHESIS")
# ---------------- actions (opportunities, risks, decisions) ----------------
for o in sorted(OPPS, key=lambda o: -o["value_m"] * o["probability"])[:4]:
    t = threat_by_comp.get(o.get("competitor"))
    action(f"ACT-{o['id']}", f"Advance {o['name']}: agree next step with the sponsor", f"{money(o['value_m'])} at {pct(o['probability'], 0)}; {o['stage']}" + (f"; {t['competitor_id']} thread {t['momentum']}" if t else ""),
           [f"EV-{o['id']}"], o["owner"], "P1" if o["value_m"] * o["probability"] >= 5 else "P2", min(o["close_date"], due_in(30)), f"{money(o['value_m'] * o['probability'])} weighted", "crm.update_field(next_step)", o["_f"], "opportunity")
for r in risks:
    if r["category"] in ("Financial", "Customer", "Operational") and r["likelihood"] >= 0.5:
        action(f"ACT-{r['id']}", r["mitigation"], r["label"], r["evidence"], r["owner"], "P2", due_in(21), r["impact_display"], "crm.create_task", r["facets"], "risk")
for d in B.get("decisions", []):
    action(f"ACT-{d['id']}", f"Decide: {d['question']}", f"Recommendation: {d['recommendation']} (confidence {pct(d['confidence'], 0)})", [f"EV-{d['id']}"], d["owner"], "P1", d["deadline"], "Sets account strategy", "decision.record", {"domain": ["pipeline"]}, "decision")
# ---------------- stakeholders ----------------
SW = {"Strong": 0.9, "Medium": 0.6, "Weak": 0.3}
STRENGTH_SYN = {"strong": "Strong", "high": "Strong", "very strong": "Strong", "medium": "Medium", "moderate": "Medium", "neutral": "Medium", "average": "Medium",
                "weak": "Weak", "low": "Weak", "poor": "Weak", "cold": "Weak"}
for x in EXECS:   # CRM vocabularies differ; unknown values stay "Unknown" (not guessed)
    x["strength"] = STRENGTH_SYN.get(str(x.get("strength", "")).strip().lower(), "Unknown")

rels = []
for x in EXECS:
    lo = [o for o in OPPS if o["id"] in x["opportunities"]]
    fac = {"stakeholder": [x["id"]], "domain": ["relationship"]}
    for dim in ("competitor", "driver", "category", "region"): fac[dim] = sorted({v for o in lo for v in o["_f"][dim]})
    rels.append({"id": x["id"], "label": x["name"], "role": x["role"], "influence": x["influence"], "strength": x["strength"], "strength_value": SW.get(x["strength"]), "trend": x["trend"],
                 "last_interaction": x["last_interaction"], "days_since_interaction": (datetime.fromisoformat(ASOF) - datetime.fromisoformat(x["last_interaction"])).days,
                 "champion": x["champion"], "risk": x["risk"], "opportunities": x["opportunities"], "evidence": [f"EV-{x['id']}"] + [f"EV-{r['signal_id']}" for r in B.get("relationship_signals", []) if r["stakeholder"] == x["id"]],
                 "confidence": 0.8, "source": x["source"], "timestamp": x["last_interaction"], "facets": fac, "drill_down_target": f"D-stk-{x['id']}", "claim_type": "FACT", "data_mode": MODE})
# ---------------- marketing ----------------
marketing = {}
if CAN_MKT and mk:
    u = mk["units"].get(ENAME, {})
    units = [{"id": k, "label": k, "direction": v["engagement_score"]["direction"], "current": v["engagement_score"]["current"], "previous": v["engagement_score"]["previous"],
              "change_display": ("new" if v["engagement_score"]["change_pct"] is None else (f"{v['engagement_score']['previous']:g} → {v['engagement_score']['current']:g} points"
                              if (v["engagement_score"]["previous"] or 0) < 5 or abs(v["engagement_score"]["change_pct"]) > 200 else spct(v["engagement_score"]["change_pct"] / 100))), "material": v["engagement_score"]["material"],
              "intent": v["buying_intent"]["current"], "surge": v["buying_intent"]["surge"]} for k, v in mk["units"].items()]
    camp_rows = []
    for cid, c in mk["campaigns"].items():
        infl = c["opportunities_influenced"]
        camp_rows.append({"id": cid, "label": next((x["name"] for x in B.get("campaigns", []) if x["campaign_id"] == cid), cid), "accounts": c["accounts"], "touches": c["touches"],
                          "influenced": [{"opportunity": i["opportunity_id"], "share": i["linear_touch_share"], "amount_display": money(i["influenced_amount"] / 1e6) if i["influenced_amount"] else None,
                                          "claim_type": i["claim_type"]} for i in infl],
                          "pipeline_influenced_display": money(sum((i["influenced_amount"] or 0) for i in infl) / 1e6), "claim_type": "CORRELATION" if all(i["claim_type"] == "CORRELATION" for i in infl) else "MIXED",
                          "facets": {"domain": ["marketing"], "opportunity": [i["opportunity_id"] for i in infl]}})
    # heatmap: category × month counts (T0)
    raw = B.get("marketing_signals_raw")
    _y, _m = int(ASOF[:4]), int(ASOF[5:7]); months6 = [f"{_y + (_m - 1 - k) // 12}-{(_m - 1 - k) % 12 + 1:02d}" for k in range(5, -1, -1)]
    cats = ["engagement", "intent", "executive", "awareness", "negative"]
    ms_objs = [{"at": x["at"], "d": json.dumps(x)} for x in mk.get("normalized_signals", []) if x["unit"] == ENAME]
    if not ms_objs and B.get("memory_db") and os.path.exists(B["memory_db"]):
        import sqlite3
        ms_objs = [dict(zip(["at", "d"], r)) for r in sqlite3.connect(B["memory_db"]).execute("SELECT observed_at, data FROM domain_objects WHERE obj_type='MarketingSignal' AND account_id=?", (ENAME,))]
    heat = [[sum(1 for m_ in ms_objs if m_["at"][:7] == mo and json.loads(m_["d"])["category"] == c) for mo in months6] for c in cats]
    timeline = sorted([{"t": m_["at"][:10], "label": json.loads(m_["d"])["type"].replace("_", " "), "category": json.loads(m_["d"])["category"], "executive": json.loads(m_["d"])["executive"],
                        "stakeholder": json.loads(m_["d"]).get("contact_id")} for m_ in ms_objs], key=lambda x: x["t"])
    marketing = {"engagement": {"current": u.get("engagement_score", {}).get("current"), "previous": u.get("engagement_score", {}).get("previous"),
                                "change_display": (lambda es: (f"{es['previous']:g} → {es['current']:g} points" if (es.get('previous') or 0) < 5 or abs(es.get('change_pct') or 0) > 200
                                                               else spct((es.get('change_pct') or 0) / 100)))(u.get("engagement_score", {})), "direction": u.get("engagement_score", {}).get("direction"), "evidence": list(MS_EV.values())[:6]},
                 "executive_engagement": {"current": (u.get("executive_engagement") or {}).get("current"), "previous": (u.get("executive_engagement") or {}).get("previous"), "roles": (u.get("executive_engagement") or {}).get("roles", [])},
                 "intent": {"current": u.get("buying_intent", {}).get("current"), "previous": u.get("buying_intent", {}).get("previous"), "surge": u.get("buying_intent", {}).get("surge"), "types": u.get("buying_intent", {}).get("types", [])},
                 "units": units, "warming": [x for x in units if x["direction"] in ("up", "new engagement")], "cooling": [x for x in units if x["direction"] == "down"],
                 "campaigns": camp_rows, "marketing_to_pipeline_display": money(sum(sum((i["influenced_amount"] or 0) for i in c["opportunities_influenced"]) for c in mk["campaigns"].values()) / 1e6),
                 "marketing_to_pipeline_claim": "CORRELATION (linear touch share; not causal)", "marketing_to_revenue": None,
                 "marketing_to_revenue_note": "Not available: needs closed-won attribution data", "events": [x for x in timeline if x["label"] in ("event attend", "webinar attend", "exec briefing attend")],
                 "content": [x for x in timeline if x["label"] == "content download"], "timeline": timeline, "heatmap": {"rows": cats, "cols": months6, "cells": heat},
                 "hypotheses": [dict(h, evidence=[MS_EV.get(x) for x in h["evidence"] if MS_EV.get(x)]) for h in mk.get("hypotheses", [])], "source": "marketing_signals.py", "data_mode": MODE}
else:
    restricted.append({"item": "Marketing intelligence", "needs": "marketing_data"}) if not CAN_MKT else None
# ---------------- financial ----------------
financial = {"public": None, "account": None}
if fi:
    lp, pp = fi["periods"][-1], fi["periods"][0]
    want = [("revenue", "Revenue", "EUR m"), ("revenue_growth", "Revenue growth", "ratio"), ("ebitda", "EBITDA", "EUR m"), ("gross_margin", "Gross margin", "ratio"), ("operating_margin", "Business operating margin", "ratio"),
            ("free_cash_flow", "Free cash flow", "EUR m"), ("fcf_margin", "FCF margin", "ratio"), ("capex", "Capex", "EUR m"), ("net_debt", "Net debt", "EUR m"), ("cash", "Cash", "EUR m"),
            ("rd_expense", "R&D", "EUR m"), ("rd_intensity", "R&D intensity", "ratio"), ("tech_investment", "Technology investment", "EUR m")]
    rows = []
    for k, lab, un in want:
        c_, p_ = fi["metrics"][lp].get(k), fi["metrics"][pp].get(k)
        f_ = (lambda x: pct(x)) if un == "ratio" else (lambda x: f"€{x:,.0f}m")
        rows.append({"id": f"fin-{k}", "label": lab, "value": c_["value"] if c_ else None, "display": f_(c_["value"]) if c_ else "Not available", "previous_display": f_(p_["value"]) if p_ else ("—" if c_ else "Not available"),
                     "delta_display": (spp(c_["value"] - p_["value"]) if un == "ratio" else spct(c_["value"] / p_["value"] - 1)) if c_ and p_ else None,
                     "direction": direction(c_["value"] - p_["value"], RATIO_TOL if un == "ratio" else 1e-9) if c_ and p_ else None, "claim_type": c_["claim_type"] if c_ else None, "confidence": c_["confidence"] if c_ else None,
                     "source": c_["inputs"][0]["source"] if c_ else None, "timestamp": c_["inputs"][0].get("source_date") if c_ else None, "formula": c_["formula"] if c_ else None,
                     "evidence": [f"EV-PUB-{lp}-{i['metric']}" for i in c_["inputs"]] if c_ else [], "available": bool(c_),
                     "missing_reason": None if c_ else next((", ".join(m_["needs"]) for m_ in fi["missing"].get(lp, []) if m_["metric"] == k), "not in the cited sources"), "data_mode": "public"})
    m25, m24 = fi["metrics"][lp], fi["metrics"][pp]
    br = [("Gross margin", m25["gross_margin"]["value"] - m24["gross_margin"]["value"]), ("R&D intensity", -(m25["rd_intensity"]["value"] - m24["rd_intensity"]["value"])),
          ("SG&A intensity", -(m25["sga_intensity"]["value"] - m24["sga_intensity"]["value"]))]
    other = (m25["operating_margin"]["value"] - m24["operating_margin"]["value"]) - sum(x for _, x in br)
    bridge = {"title": f"Business operating margin bridge, {pp} → {lp}", "unit": "pp",
              "steps": [{"label": pp, "value": round(m24["operating_margin"]["value"] * 100, 2), "display": pct(m24["operating_margin"]["value"]), "kind": "start"}] +
                       [{"label": l_, "value": round(x * 100, 2), "display": spp(x, 2), "kind": "delta"} for l_, x in br + [("Other income and expense", other)]] +
                       [{"label": lp, "value": round(m25["operating_margin"]["value"] * 100, 2), "display": pct(m25["operating_margin"]["value"]), "kind": "end"}],
              "method": "Intensity changes computed from cited business (non-IFRS) figures; 'other' is the residual", "evidence": [f"EV-PUB-{lp}-operating_income", f"EV-PUB-{lp}-gross_profit"]}
    opex = [{"label": "R&D", "value": m25["rd_expense"]["value"], "display": f"€{m25['rd_expense']['value']:,.0f}m"}, {"label": "SG&A", "value": m25["sga_expense"]["value"], "display": f"€{m25['sga_expense']['value']:,.0f}m"}]
    drivers_f = [{"id": f"FD-{s['signal_id']}", "what_changed": s["text"], "why_it_matters": next((i["implication"] for i in fi["commercial_implications"] if i["signal"] == s["kind"]), ""),
                  "implication": next((i["implication"] for i in fi["commercial_implications"] if i["signal"] == s["kind"]), ""), "claim_type": "HYPOTHESIS", "signal_claim_type": s["claim_type"],
                  "confidence": s["confidence"], "evidence": [f"EV-{s['signal_id']}"], "facets": {"domain": ["financial"]}} for s in fi["signals"]]
    financial["public"] = {"entity": ENAME, "periods": fi["periods"], "metrics": rows, "missing": [r["label"] for r in rows if not r["available"]], "bridge": bridge,
                           "investment_mix": {"title": f"Operating expense mix, {lp}", "items": opex, "evidence": [f"EV-PUB-{lp}-rd_expense", f"EV-PUB-{lp}-sga_expense"]},
                           "drivers": drivers_f, "sensitivity": fi["sensitivity"], "note": "Published figures; business (non-IFRS) measures as reported by the company"}
acc_signals = []
if CAN_FIN and HAS_Q:
    cts = [q["cost_to_serve_m"] / q["revenue_m"] for q in Q]; bk = [q["bookings_m"] for q in Q]
    def asig(k, lab, series, good_up, fmtf, unit_is_ratio):
        for lag, nm in ((1, "QoQ"), (4, "YoY")):
            d = series[-1] - series[-1 - lag]
            if fmtf(series[-1]) == fmtf(series[-1 - lag]): d = 0.0          # displayed values equal → flat and neutral
            acc_signals.append({"id": f"AFS-{k}-{nm}", "label": f"{lab} {nm}", "text": f"{lab} {fmtf(series[-1 - lag])} → {fmtf(series[-1])} ({nm})", "delta": round(d, 4),
                                "direction": direction(d), "sentiment": senti(d, good_up), "domain": "financial", "timestamp": ASOF, "claim_type": "FACT", "confidence": 0.9,
                                "source": Q[-1]["source"], "evidence": [f"EV-Q-{Q[-1]['quarter']}", f"EV-Q-{Q[-1 - lag]['quarter']}"], "facets": {"domain": ["financial"]}, "data_mode": MODE})
    asig("rev", "Account revenue", q_rev, True, lambda x: money(x, 2), False); asig("gm", "Account gross margin", gm, True, pct, True); asig("dso", "DSO", dso, False, lambda x: f"{x:.0f} days", False)
    asig("cts", "Cost to serve", cts, False, pct, True); asig("bk", "Bookings", bk, True, lambda x: money(x, 2), False)
    BU = B.get("business_units") or []                     # business-unit data comes from the PROVIDER; none → shown as unavailable
    financial["account"] = {"quarters": [q["quarter"] for q in Q], "revenue": [{"t": q["quarter"], "v": q["revenue_m"]} for q in Q], "margin": [{"t": q["quarter"], "v": round(g, 4)} for q, g in zip(Q, gm)],
                            "dso": [{"t": q["quarter"], "v": round(d, 1)} for q, d in zip(Q, dso)], "signals": acc_signals,
                            "revenue_mix": {"title": "Account revenue by business unit (TTM)", "items": [{"label": b["name"], "value": b["revenue_ttm_m"], "display": money(b["revenue_ttm_m"]),
                                            "growth_display": spct(b["revenue_ttm_m"] / b["revenue_prev_ttm_m"] - 1)} for b in BU], "basis": BU[0]["source"] if BU else "not available", "evidence": ["EV-SERIES"]},
                            "bu_performance": [{"label": b["name"], "revenue_display": money(b["revenue_ttm_m"]), "growth_display": spct(b["revenue_ttm_m"] / b["revenue_prev_ttm_m"] - 1),
                                                "margin_display": pct(b["gross_margin"]), "direction": direction(b["revenue_ttm_m"] - b["revenue_prev_ttm_m"])} for b in BU],
                            "bu_note": None if BU else "Business-unit data not provided by the data source",
                            "source": Q[-1]["source"], "data_mode": MODE}
# ---------------- signals (unified) ----------------
signals = []
for s in (fi or {}).get("signals", []):
    signals.append({"id": s["signal_id"], "label": s["text"], "domain": "financial", "timestamp": "2026-01-29", "claim_type": s["claim_type"], "confidence": s["confidence"], "source": EVID[f"EV-{s['signal_id']}"]["source"],
                    "evidence": [f"EV-{s['signal_id']}"], "facets": {"domain": ["financial"]}, "data_mode": "public"})
signals += acc_signals
for t in threads:
    for c in t["chronology"]:
        signals.append({"id": f"SIG-{t['id']}-{c['t']}", "label": f"{t['competitor']}: {c['text']}", "domain": "competitive", "timestamp": c["t"], "claim_type": "FACT", "confidence": 0.8,
                        "source": EVID[c["evidence"]]["source"] if c["evidence"] else "competitive_threads.py", "evidence": [c["evidence"]] if c["evidence"] else [], "facets": t["facets"], "data_mode": MODE})
if marketing:
    for i, x in enumerate(marketing["timeline"]):
        signals.append({"id": f"SIG-MK-{i}", "label": f"Marketing: {x['label']}" + (" (executive)" if x["executive"] else ""), "domain": "marketing", "timestamp": x["t"], "claim_type": "FACT", "confidence": 0.85,
                        "source": "marketing automation", "evidence": [], "facets": {"domain": ["marketing"], **({"stakeholder": [x["stakeholder"]]} if x["stakeholder"] else {})}, "data_mode": MODE})
for r in B.get("relationship_signals", []):
    signals.append({"id": f"SIG-{r['signal_id']}", "label": f"Relationship: {r['kind'].replace('_', ' ')} ({r['stakeholder']})", "domain": "relationship", "timestamp": r["observed_at"], "claim_type": "FACT", "confidence": 0.8,
                    "source": r["source"], "evidence": [f"EV-{r['signal_id']}"], "facets": {"domain": ["relationship"], "stakeholder": [r["stakeholder"]]}, "data_mode": MODE})
signals.sort(key=lambda s: s["timestamp"] or "", reverse=True)
# ---------------- What changed (delta) ----------------
DOM = {"financial_state": "financial", "marketing_state": "marketing", "competitive_state": "competitive", "relationship_state": "relationship", "commercial_state": "pipeline", "market_state": "market", "operational_state": "operational"}
CUSTOMER_KEYS = {"csat", "open_escalations"}
GOOD_DOWN = {"account_dso_days", "cost_to_serve_ratio", "open_escalations"}
LAB = {"account_revenue_ttm": ("Revenue (TTM)", "money"), "account_gross_margin_month": ("Account gross margin (month)", "pct"), "account_dso_days": ("DSO (days)", "num"), "cost_to_serve_ratio": ("Cost to serve", "pct"),
       "engagement_score": ("Engagement score (rolling 90 days)", "num"), "executive_touches": ("Executive touches (rolling 90 days)", "num"), "intent_signals": ("Intent signals (rolling 90 days)", "num"), "pipeline_total_m": ("Pipeline", "money"),
       "sla_attainment": ("SLA attainment", "pct"), "open_escalations": ("Open escalations", "num"), "csat": ("Customer satisfaction", "num")}
def fmtv(k, x):
    kind = LAB.get(k, (None, None))[1]
    if isinstance(x, (int, float)) and not isinstance(x, bool):
        if kind == "money": return money(x)
        if kind == "pct" or (k.endswith(":probability")): return pct(x, 1 if kind == "pct" else 0)
        return f"{x:g}"
    return str(x)
changes = []
dl = B.get("delta") or {"domains": {}}
cur_dom = (B.get("delta_snapshots") or {}).get("current", {}).get("domains", {})
if not CAN_FIN: dl = {"domains": {k: v for k, v in dl["domains"].items() if k != "financial_state"}}
for dname, rec in dl["domains"].items():
    for ctype, items in rec.items():
        for it in items:
            key = it["key"] if isinstance(it, dict) else it
            cr = cur_dom.get(dname, {}).get(key, {}) if isinstance(cur_dom.get(dname, {}).get(key, {}), dict) else {}
            dom = "customer" if key in CUSTOMER_KEYS else DOM.get(dname, "customer")
            frm = it.get("from") if isinstance(it, dict) else None; to = it.get("to") if isinstance(it, dict) else (cr.get("value") if ctype == "new" else None)
            num = isinstance(frm, (int, float)) and isinstance(to, (int, float)) and not isinstance(frm, bool)
            d = (to - frm) if num else None
            good_up = key not in GOOD_DOWN
            if isinstance(to, str) and isinstance(frm, str):
                ordm = {"Low": 1, "Medium": 2, "High": 3, "Weak": 1, "Strong": 3}
                if frm in ordm and to in ordm: d = ordm[to] - ordm[frm]; good_up = not key.endswith(":risk")
            label = LAB.get(key, (key.replace(":", " · ").replace("_", " "), None))[0]
            if key.split(":")[0].startswith("OPP-"): label = next((o["name"] for o in OPPS if o["id"] == key.split(":")[0]), key) + " · " + key.split(":")[1].replace("_", " ")
            if key.split(":")[0].startswith("C-"): label = next((f"{x['role']} ({x['name']})" for x in EXECS if x["id"] == key.split(":")[0]), key) + " · " + key.split(":")[1].replace("_", " ")
            fac = {"domain": [dom]}
            if key.startswith("Competitor"): fac["competitor"] = [key.split(":")[0]]
            if key.startswith("OPP-"): fac.update(next(o["_f"] for o in OPPS if o["id"] == key.split(":")[0]))
            if key.startswith("C-"): fac["stakeholder"] = [key.split(":")[0]]
            src_ = cr.get("source") or ("multiple sources (see claims)" if ctype == "contradictory" else "delta engine")
            changes.append({"id": f"CHG-{dname}-{key}".replace(" ", "_"), "label": label, "domain": dom, "change_type": ctype,
                            "previous_value": frm, "previous_display": fmtv(key, frm) if frm is not None else ("—" if ctype == "new" else None),
                            "value": to, "display": fmtv(key, to) if to is not None else ("removed" if ctype == "deleted" else "conflicting"),
                            "delta": round(d, 4) if isinstance(d, float) else d, "delta_display": (smoney(d) if LAB.get(key, (0, 0))[1] == "money" else spp(d) if (LAB.get(key, (0, 0))[1] == "pct" or key.endswith(":probability")) else f"{d:+g}") if num else None,
                            "direction": direction(d) if d is not None else None, "sentiment": senti(d, good_up) if d is not None else ("negative" if ctype == "contradictory" else "neutral"),
                            "timestamp": cr.get("as_of") or dl.get("to") or ASOF, "date": cr.get("as_of") or ASOF, "confidence": 0.4 if ctype == "contradictory" else 0.8 if ctype == "corrected" else 0.85,
                            "source": src_, "evidence": [], "claims": it.get("claims") if isinstance(it, dict) else None, "facets": fac, "drill_down_target": None, "claim_type": "FACT" if ctype != "contradictory" else "INFERENCE", "data_mode": MODE})
for c in changes:
    eid = ev(f"EV-{c['id']}", c["source"], c["date"], f"{c['label']}: {c['previous_display']} → {c['display']} ({c['change_type']})", c["confidence"], c["claim_type"],
             hist=f"Previous snapshot {dl.get('from') or 'n/a'}"); c["evidence"] = [eid]; c["drill_down_target"] = f"D-chg-{c['id']}"
changes.sort(key=lambda c: (c["sentiment"] != "negative", -abs(c["delta"]) if isinstance(c["delta"], (int, float)) else 0))
# ---------------- narrative (T0, evidence-linked) ----------------
pos = [c for c in changes if c["sentiment"] == "positive"][:5]; neg = [c for c in changes if c["sentiment"] == "negative"][:5]
hi_threats = [t for t in threads if t["status"] == "active" and t["risk"] == "High"]
summary = ([{"text": f"Revenue from {ENAME} reached {money(ttm)} over the last twelve months, {spct(ttm / pttm - 1)} on the prior twelve.", "claim_type": "FACT", "evidence": ["EV-SERIES"]}] if HAS_S else
           [{"text": f"Annual revenue from {ENAME} is {money(B['revenue_annual_m'])} (CRM account record); no billing history is available, so growth cannot be computed.", "claim_type": "FACT", "evidence": []}] if B.get("revenue_annual_m") else []) + ([
           {"text": (lambda top: f"Growth potential stands at {money(gp)} across {len(OPPS)} opportunities; {top['label'].lower()} is the largest driver at {top['display']}.")(max(drivers['children'], key=lambda c: c['value'])), "claim_type": "DERIVED", "evidence": [f"EV-{o['id']}" for o in OPPS][:4]}] if HAS_GROWTH else
           [{"text": f"Pipeline stands at {money(pipe)} across {len(OPPS)} open opportunities; growth potential cannot be sized because opportunities carry no incremental growth value.", "claim_type": "DERIVED", "evidence": [f"EV-{o['id']}" for o in OPPS][:4]}] if OPPS else [])
if marketing and marketing["engagement"]["direction"] in ("up", "new engagement"):
    summary.append({"text": f"Marketing engagement is rising ({marketing['engagement']['change_display']}, last 90 days vs the previous 90) with {marketing['executive_engagement']['current']} executive touches and {marketing['intent']['current']} intent signals in the last 90 days.", "claim_type": "FACT", "evidence": marketing["engagement"]["evidence"][:4]})
if hi_threats:
    t = hi_threats[0]; lo = [o for o in opps if o["id"] in t["opportunities"]]
    summary.append({"text": f"However, competitive pressure is accelerating: {len(hi_threats)} high-risk threads, led by {t['competitor']} ({t['signal_count']} signals){' on the ' + money(lo[0]['value']) + ' ' + lo[0]['label'].lower() if lo else ''}.", "claim_type": "INFERENCE", "evidence": t["evidence"][:4]})
if CAN_FIN and HAS_Q and gm[-1] < gm[-5]:
    summary.append({"text": f"Account gross margin has eased from {pct(gm[-5])} to {pct(gm[-1])} over four quarters, and value at risk is {money(rx)}.", "claim_type": "FACT", "evidence": [f"EV-Q-{Q[-1]['quarter']}", f"EV-Q-{Q[-5]['quarter']}"]})
narrative = {"summary": summary, "positive": [{"id": c["id"], "text": f"{c['label']}: {c['previous_display']} → {c['display']}", "delta_display": c["delta_display"], "evidence": c["evidence"], "domain": c["domain"]} for c in pos],
             "negative": [{"id": c["id"], "text": f"{c['label']}: {c['previous_display']} → {c['display']}", "delta_display": c["delta_display"], "evidence": c["evidence"], "domain": c["domain"]} for c in neg],
             "method": "Generated by dashboard_builder.py from computed metrics and detected changes; every sentence cites evidence. The dashboard agent may rephrase at T2 but must keep the evidence.",
             "generated_by": "T0 template over computed facts"}
# ---------------- SWOT ----------------
def sw(text, evid, src_, dt, conf, trend, impact, ct="FACT"): return {"text": text, "evidence": [e_ for e_ in evid if e_], "source": src_, "date": dt, "confidence": conf, "trend": trend, "impact": impact, "claim_type": ct}
strong = [x for x in EXECS if x["strength"] == "Strong"]; weak_hi = [x for x in EXECS if x["strength"] == "Weak" and x["influence"] >= 0.6]
swot = {"strengths": [sw(f"{len(strong)} strong executive relationships including {', '.join(x['role'] for x in strong[:2])}", [f"EV-{x['id']}" for x in strong], strong[0]["source"], ASOF, 0.8, "up", "High"),
                     ] + [sw(f"Incumbent on the {money(o['value_m'])} {o['name']}", [f"EV-{o['id']}"], o["source"], o.get("created_at"), 0.85, "flat", "High") for o in OPPS if o["category"] == "Renewal"][:2],
        "weaknesses": [sw(f"Weak relationships with {len(weak_hi)} influential executives ({', '.join(x['role'] for x in weak_hi[:3])})", [f"EV-{x['id']}" for x in weak_hi], weak_hi[0]["source"] if weak_hi else "CRM", ASOF, 0.8, "down", "High")] +
                      ([sw(f"Account margin eased {spp(gm[-1] - gm[-5])} over four quarters", [f"EV-Q-{Q[-1]['quarter']}"], Q[-1]["source"], ASOF, 0.9, "down", "Medium")] if CAN_FIN else []) +
                      [sw(f"SLA attainment slipped to {pct(ops['sla_attainment']['value'])}", ["EV-OPS-sla_attainment"], ops["sla_attainment"]["source"], ASOF, 0.85, "down", "Medium")] if "sla_attainment" in ops else [],
        "opportunities": [sw(f"{o['label']}: {o['display']} at {o['probability_display']}", o["evidence"][:2], o["source"], o["timestamp"], o["confidence"], o["direction"] or "flat", "High" if o["value"] >= 5 else "Medium", "HYPOTHESIS")
                          for o in sorted(opps, key=lambda o: -o["value"] * o["probability"]) if o["category"] != "Renewal"][:3] +
                         [sw(f"{t['competitor']} weakening: displacement opportunity ({t['opportunity_level']})", t["evidence"][:2], "competitive_threads.py", t["latest_signal"], t["confidence"], "up", t["opportunity_level"], "INFERENCE")
                          for t in threads if t["thread_type"] == "displacement_opportunity" and t["status"] == "active"][:2],
        "threats": [sw(f"{t['competitor']}: {t['momentum']}, risk {t['risk']}, {t['signal_count']} signals", t["evidence"][:3], "competitive_threads.py", t["latest_signal"], t["confidence"], "up" if t["momentum"] == "accelerating" else "flat", t["risk"], "INFERENCE")
                    for t in hi_threats] + [sw(r_["label"], r_["evidence"], r_["source"], ASOF, r_["confidence"], "up", "High" if r_["impact"] >= 0.5 else "Medium", r_["claim_type"]) for r_ in risks if r_["category"] == "Customer"][:2]}
# ---------------- health (8 dimensions, no composite; a dimension without data says so) ----------------
def dim(id_, label, score, basis, trend, evid):
    s_ = max(0, min(100, round(score)))
    return {"id": id_, "label": label, "score": s_, "status": "healthy" if s_ >= 70 else "watch" if s_ >= 45 else "at risk", "basis": basis, "trend": trend, "evidence": [e_ for e_ in evid if e_]}
def nodim(id_, label, needs, status="no data"):
    return {"id": id_, "label": label, "score": None, "status": status, "basis": f"Not available: needs {needs}" if status == "no data" else "Restricted for this role", "trend": None, "evidence": []}
HX = [x for x in EXECS if SW.get(x["strength"]) is not None and x.get("influence") is not None]
dims = []
if not CAN_FIN: dims.append(nodim("financial", "Financial", "", "restricted"))
elif len(Q) >= 5:
    dims.append(dim("financial", "Financial", 70 + (gm[-1] - gm[-5]) * 1000 - (dso[-1] - dso[-5]) * 2, f"Margin {spp(gm[-1] - gm[-5])} and DSO {dso[-1] - dso[-5]:+.0f} days over 4 quarters",
                    "down" if gm[-1] < gm[-5] else "flat", [f"EV-Q-{Q[-1]['quarter']}"]))
else: dims.append(nodim("financial", "Financial", "5 quarters of account P&L"))
if "csat" in ops and "open_escalations" in ops:
    dims.append(dim("customer", "Customer", 100 * (ops["csat"]["value"] - 1) / 4 - 8 * ops["open_escalations"]["value"], f"CSAT {ops['csat']['value']}, {ops['open_escalations']['value']} open escalations",
                    "down" if ops["csat"]["value"] < ops["csat"]["previous"] else "flat", ["EV-OPS-csat", "EV-OPS-open_escalations"]))
else: dims.append(nodim("customer", "Customer", "CSAT and escalation data"))
if HX:
    rel_score = 100 * sum(x["influence"] * SW[x["strength"]] for x in HX) / sum(x["influence"] for x in HX)
    dims.append(dim("relationship", "Relationship", rel_score, f"Influence-weighted relationship strength across {len(HX)} executives" + (f" ({len(EXECS) - len(HX)} without a recognized strength)" if len(HX) < len(EXECS) else ""),
                    "down" if any(r["kind"] == "champion_weakening" for r in B.get("relationship_signals", [])) else "flat", [f"EV-{r['signal_id']}" for r in B.get("relationship_signals", [])] or [f"EV-{x['id']}" for x in HX[:3]]))
else: dims.append(nodim("relationship", "Relationship", "contacts with relationship strength and influence"))
if marketing and marketing.get("engagement", {}).get("current") is not None:
    dims.append(dim("marketing", "Marketing", 55 + min(35, (marketing["engagement"]["current"] or 0) - (marketing["engagement"]["previous"] or 0)),
                    f"Engagement {marketing['engagement']['change_display']}, intent surge: {'yes' if marketing['intent']['surge'] else 'no'}", marketing["engagement"]["direction"], marketing["engagement"]["evidence"][:3]))
else: dims.append(nodim("marketing", "Marketing", "marketing signals (or marketing_data access)"))
if thr:
    dims.append(dim("competitive", "Competitive", 100 - 25 * len(hi_threats) - 10 * sum(1 for t in threads if t["status"] == "active" and t["risk"] == "Medium") + 5 * sum(1 for t in threads if t["thread_type"] == "displacement_opportunity" and t["status"] == "active"),
                    f"{len(hi_threats)} high-risk threads; competitive exposure {pct(cx, 0) if cx is not None else 'n/a'}", "down" if hi_threats else "flat", [e_ for t in hi_threats for e_ in t["evidence"][:2]]))
else: dims.append(nodim("competitive", "Competitive", "competitive signals (Competitive Thread memory)"))
if OPPS and pipe:
    dims.append(dim("commercial", "Commercial", 50 + 100 * (fc / pipe - 0.4) + 20 * ((pipe - pipe_prev) / pipe_prev if pipe_prev else 0), f"Weighted forecast {money(fc)} on {money(pipe)} pipeline ({pct(fc / pipe, 0)} weighted)",
                    direction(fc - fc_prev) if fc_prev is not None else "flat", [f"EV-{o['id']}" for o in OPPS[:3]]))
else: dims.append(nodim("commercial", "Commercial", "open opportunities"))
if "sla_attainment" in ops:
    bl = ops.get("backlog", {}).get("value")
    dims.append(dim("operational", "Operational", 100 * ops["sla_attainment"]["value"] - 30 - (0.1 * (bl - 100) if bl is not None else 0), f"SLA {pct(ops['sla_attainment']['value'])}" + (f", backlog {bl}" if bl is not None else ""),
                    "down" if ops["sla_attainment"]["value"] < ops["sla_attainment"]["previous"] else "flat", ["EV-OPS-sla_attainment"] + (["EV-OPS-backlog"] if bl is not None else [])))
else: dims.append(nodim("operational", "Operational", "service operations KPIs (SLA, backlog)"))
SI = [o for o in OPPS if o.get("strategic_impact") is not None and o.get("value_m")]
if SI:
    p5 = "P5" in (B.get("correlation") or {}).get("detected", [])
    dims.append(dim("strategic", "Strategic", 40 + 60 * sum(o["strategic_impact"] * o["value_m"] for o in SI) / sum(o["value_m"] for o in SI) * (1 if p5 else 0.8),
                    "Strategic-impact-weighted pipeline; compound cross-domain pattern " + ("detected" if p5 else "not detected"), "up" if p5 else "flat", [f"EV-{o['id']}" for o in SI[:2]]))
else: dims.append(nodim("strategic", "Strategic", "strategic impact per opportunity"))
health = {"dimensions": dims, "note": "Eight dimensions shown separately; no single composite score. A dimension without data is marked 'no data'. Rules in references/metric-definitions.md."}
# ---------------- scenarios (T0, MODELED) ----------------
# Scenario engine (T0). WHICH scenarios to run is data (bundle["scenario_specs"]); without specs, a generic set is derived:
# loss of the largest contested deal (term 1 year, stated as an assumption) and a slip of the two largest deals.
OBYID = {o["id"]: o for o in OPPS}
specs = B.get("scenario_specs")
if not specs:
    cands = sorted([o for o in OPPS if contested(o)], key=lambda o: -o["value_m"])
    specs = ([{"type": "opportunity_loss", "opportunity": cands[0]["id"], "term_years": 1, "dependent_opportunities": []}] if cands else []) + [{"type": "slip", "top_n": 2, "days": 90}]
scen = []
def srow(k, lab, base, sc): return {"metric": lab, "baseline": money(base[k]), "scenario": money(sc[k]), "delta": smoney(sc[k] - base[k]), "delta_value": round(sc[k] - base[k], 2)}
for sp in specs:
    o = OBYID.get(sp.get("opportunity"))
    if sp["type"] == "opportunity_loss" and o:
        term = sp.get("term_years", 1); acv = o["value_m"] / term; dep = [OBYID[d] for d in sp.get("dependent_opportunities", []) if d in OBYID]
        base = {"revenue_run_rate": ttm, "pipeline": pipe, "forecast": fc, "growth_potential": gp, "value_at_risk": rx}
        lost_pipe = o["value_m"] + sum(d["value_m"] for d in dep); lost_fc = o["value_m"] * o["probability"] + sum(d["value_m"] * d["probability"] for d in dep)
        rev_hit = acv if o["category"] == "Renewal" else 0.0
        sc = {"revenue_run_rate": ttm - rev_hit, "pipeline": pipe - lost_pipe, "forecast": fc - lost_fc, "growth_potential": gp - o["growth_value_m"] - sum(d["growth_value_m"] for d in dep),
              "value_at_risk": rx - (o["value_m"] * (1 - o["probability"]) if contested(o) else 0)}
        who = o.get("competitor") or "a competitor"
        th_ev = [e_ for t in threads if t["competitor"] == o.get("competitor") for e_ in t["evidence"][:2]]
        scen.append({"id": f"SC-LOSS-{o['id']}", "label": f"{who} wins the {o['category'].lower()}", "question": f"What happens if {who} wins this {money(o['value_m'])} {o['category'].lower()}?",
                     "assumptions": [f"Contract term {term} year{'s' if term != 1 else ''} → annual value {money(acv, 2)}" + (" leaves the revenue run rate" if rev_hit else " (not yet in the run rate)")] +
                                    [sp.get("dependency_note") or f"{d['name']} is lost with it" for d in dep][:1] + ["No change to other opportunities; no pricing response modeled"],
                     "baseline": base, "scenario": sc, "delta": {k: round(sc[k] - base[k], 2) for k in base},
                     "rows": [srow(k, l_, base, sc) for k, l_ in (("revenue_run_rate", "Revenue run rate"), ("pipeline", "Pipeline"), ("forecast", "Weighted forecast"), ("growth_potential", "Growth potential"), ("value_at_risk", "Value at risk"))],
                     "impacts": {"financial": f"Annual revenue {smoney(-rev_hit)}", "pipeline": f"Pipeline {smoney(-lost_pipe)}",
                                 "risk": f"{who} gains the position; value at risk falls only because the contested deal is gone", "opportunity": f"Growth potential {smoney(sc['growth_potential'] - gp)}"},
                     "variants": [{"label": f"{int(p_ * 100)}% chance of loss", "expected_revenue_impact": smoney(-rev_hit * p_), "expected_forecast_impact": smoney(-lost_fc * p_)} for p_ in (0.3, 0.5, 1.0)],
                     "confidence": 0.55, "modeled": True, "claim_type": "MODELED", "evidence": [f"EV-{o['id']}"] + [f"EV-{d['id']}" for d in dep] + th_ev,
                     "source": "dashboard_builder.py scenario engine (T0)", "timestamp": ASOF, "facets": {"competitor": [o["competitor"]] if o.get("competitor") else [], "domain": ["pipeline"]}, "data_mode": MODE})
    elif sp["type"] == "opportunity_win" and o:
        term = sp.get("term_years", 1); acv = o["value_m"] / term
        base = {"revenue_run_rate": ttm, "pipeline": pipe, "forecast": fc}; sc = {"revenue_run_rate": ttm + acv, "pipeline": pipe - o["value_m"], "forecast": fc + o["value_m"] * (1 - o["probability"])}
        scen.append({"id": f"SC-WIN-{o['id']}", "label": f"{o['name']} closes", "question": f"What if the {money(o['value_m'])} {o['name']} closes?",
                     "assumptions": [f"Term {term} year{'s' if term != 1 else ''} → {money(acv, 2)} annual revenue", "Moves from pipeline to booked"],
                     "baseline": base, "scenario": sc, "delta": {k: round(sc[k] - base[k], 2) for k in base},
                     "rows": [srow(k, l_, base, sc) for k, l_ in (("revenue_run_rate", "Revenue run rate"), ("pipeline", "Pipeline"), ("forecast", "Weighted forecast"))],
                     "impacts": {"financial": f"Annual revenue {smoney(acv)}", "pipeline": f"Pipeline {smoney(-o['value_m'])} (converted)",
                                 "risk": f"Removes the {o['competitor']} threat on this deal" if o.get("competitor") else "No competitor on this deal", "opportunity": "Adjacent use cases become reachable"},
                     "variants": [], "confidence": 0.5, "modeled": True, "claim_type": "MODELED", "evidence": [f"EV-{o['id']}"], "source": "dashboard_builder.py scenario engine (T0)", "timestamp": ASOF,
                     "facets": {"competitor": [o["competitor"]] if o.get("competitor") else [], "domain": ["pipeline"]}, "data_mode": MODE})
    elif sp["type"] == "slip":
        top = sorted(OPPS, key=lambda o: -o["value_m"])[:sp.get("top_n", 2)]; fy_end = f"{ASOF[:4]}-12-31"
        slip = sum(o["value_m"] * o["probability"] for o in top if o["close_date"] <= fy_end)
        scen.append({"id": "SC-SLIP", "label": f"{len(top)} largest deals slip {sp.get('days', 90)} days", "question": f"What if the {len(top)} largest opportunities slip {sp.get('days', 90)} days?",
                     "assumptions": [f"Close dates move {sp.get('days', 90)} days", "Probabilities unchanged", f"Only deals closing by {fy_end} affect this fiscal year"],
                     "baseline": {"fy_forecast": fc}, "scenario": {"fy_forecast": fc - slip}, "delta": {"fy_forecast": round(-slip, 2)},
                     "rows": [{"metric": "Weighted forecast closing this fiscal year", "baseline": money(fc), "scenario": money(fc - slip), "delta": smoney(-slip), "delta_value": round(-slip, 2)}],
                     "impacts": {"financial": f"In-year bookings {smoney(-slip)}", "pipeline": "Pipeline unchanged; it ages by one quarter", "risk": "Forecast credibility", "opportunity": "None"},
                     "variants": [], "confidence": 0.6, "modeled": True, "claim_type": "MODELED", "evidence": [f"EV-{o['id']}" for o in top], "source": "dashboard_builder.py scenario engine (T0)",
                     "timestamp": ASOF, "facets": {"domain": ["pipeline"]}, "data_mode": MODE})
renew = next((OBYID[s_["opportunity"]] for s_ in specs if s_["type"] == "opportunity_loss" and s_.get("opportunity") in OBYID), None)
for s_ in scen: s_["display"] = s_["rows"][0]["delta"]
# ---------------- comparisons ----------------
def crow(lab, a_, b_, fmt, good_up=True):
    d = (a_ - b_) if isinstance(a_, (int, float)) and isinstance(b_, (int, float)) else None
    return {"label": lab, "a": fmt(a_) if a_ is not None else "—", "b": fmt(b_) if b_ is not None else "—", "delta": (smoney(d) if fmt is money else spp(d) if fmt in (pct,) else f"{d:+,.1f}") if d is not None else None, "direction": direction(d), "sentiment": senti(d, good_up)}
regions = sorted({o["region"] for o in OPPS})
# Comparison modes: each is included only when its inputs exist; the rest are listed with what they need.
comparisons, comparisons_unavailable = {}, {}
def cmp_add(key, needs, build):
    try:
        v = build()
        if v: comparisons[key] = v; return
    except (KeyError, IndexError, TypeError, ZeroDivisionError):
        pass
    comparisons_unavailable[key] = needs
cmp_add("current_vs_previous", "metrics with a previous value", lambda: {"label": "Current vs previous", "a_label": "Current", "b_label": "Previous",
        "rows": [crow(m["label"], m["value"], m["previous_value"], money if m["unit"] == "USD m" else pct) for m in metrics if m.get("value") is not None and m.get("previous_value") is not None]} if any(m.get("previous_value") is not None for m in metrics) else None)
cmp_add("actual_vs_target", "monthly revenue with targets", lambda: {"label": "Actual vs target", "a_label": "Actual", "b_label": "Target",
        "rows": [crow("Revenue (TTM)", ttm, sum(S["target"][-12:]), money), crow("Revenue (last quarter)", sum(rev[-3:]), sum(S["target"][-3:]), money)]} if HAS_S and S.get("target") else None)
cmp_add("actual_vs_forecast", "a prior forecast for recent months", lambda: {"label": "Actual vs forecast", "a_label": "Actual", "b_label": "Prior forecast",
        "rows": [crow(m_, a_, b_, money) for m_, a_, b_ in zip(S["prior_forecast"]["months"], rev[-len(S["prior_forecast"]["months"]):], S["prior_forecast"]["values"])]} if HAS_S and S.get("prior_forecast") else None)
cmp_add("region_vs_region", "opportunities with regions", lambda: {"label": "Region vs region", "columns": regions, "rows": [
        {"label": "Pipeline", "values": [money(agg(lambda o: o["value_m"], lambda o, r=r: o["region"] == r)) for r in regions]},
        {"label": "Weighted forecast", "values": [money(agg(lambda o: o["value_m"] * o["probability"], lambda o, r=r: o["region"] == r)) for r in regions]},
        {"label": "Opportunities", "values": [str(sum(1 for o in OPPS if o["region"] == r)) for r in regions]}]} if len(regions) >= 2 else None)
cmp_add("account_vs_account", "peer accounts", lambda: {"label": "Account vs account", "columns": [ENAME] + [p_["account"] for p_ in B["peers"]], "rows": [
        {"label": "Revenue (TTM)", "values": [money(ttm) or "Not available"] + [money(p_["revenue_m"]) for p_ in B["peers"]]},
        {"label": "Growth", "values": [spct(ttm / pttm - 1) if ttm and pttm else "Not available"] + [spct(p_["revenue_m"] / p_["prev_revenue_m"] - 1) for p_ in B["peers"]]},
        {"label": "Pipeline", "values": [money(pipe)] + [money(p_["pipeline_m"]) for p_ in B["peers"]]}]} if B.get("peers") else None)
cmp_add("competitor_vs_competitor", "two or more competitors", lambda: {"label": "Competitor vs competitor", "columns": [c["label"] for c in landscape], "rows": [
        {"label": "Threat", "values": [c["threat"] for c in landscape]}, {"label": "Overlap value", "values": [c["overlap_display"] for c in landscape]},
        {"label": "Signals (90 days)", "values": [str(c["activity_90d"]) for c in landscape]}, {"label": "Momentum", "values": [c["momentum"] for c in landscape]}]} if len(landscape) >= 2 else None)
cmp_add("quarter_vs_quarter", "two quarters of account P&L", lambda: {"label": "Quarter vs quarter", "a_label": Q[-1]["quarter"], "b_label": Q[-2]["quarter"],
        "rows": [crow("Account revenue", q_rev[-1], q_rev[-2], money)] + ([crow("Account gross margin", gm[-1], gm[-2], pct)] if CAN_FIN else [])} if len(Q) >= 2 else None)
cmp_add("year_vs_year", "five quarters of account P&L or two years of published financials", lambda: ({"label": "Year vs year", "a_label": Q[-1]["quarter"], "b_label": Q[-5]["quarter"],
        "rows": [crow("Account revenue", q_rev[-1], q_rev[-5], money)] + ([crow("Account gross margin", gm[-1], gm[-5], pct)] if CAN_FIN else [])} if len(Q) >= 5 else
        ({"label": "Year vs year", "a_label": "", "b_label": "", "rows": []} if fi and len(fi.get("periods", [])) >= 2 else None)))
if fi and "year_vs_year" in comparisons:
    comparisons["year_vs_year"]["public"] = {"a_label": fi["periods"][-1], "b_label": fi["periods"][0], "rows": [{"label": r["label"], "a": r["display"], "b": r["previous_display"], "delta": r["delta_display"], "direction": r["direction"]} for r in financial["public"]["metrics"] if r["available"]][:6]}
# ---------------- tables ----------------
tables = {"accounts": {"columns": [{"id": "account", "label": "Account", "type": "text"}, {"id": "revenue", "label": "Revenue", "type": "money"}, {"id": "growth", "label": "Growth", "type": "pct"},
                                   {"id": "pipeline", "label": "Pipeline", "type": "money"}, {"id": "risk", "label": "Risk", "type": "level"}, {"id": "trend", "label": "Trend", "type": "spark"}],
                       "rows": [{"id": E["id"], "cells": {"account": ENAME, "revenue": {"v": ttm, "d": money(ttm) or "Not available"}, "growth": {"v": (ttm / pttm - 1) if ttm and pttm else None, "d": spct(ttm / pttm - 1) if ttm and pttm else "Not available"}, "pipeline": {"v": pipe, "d": money(pipe)},
                                                         "risk": "Medium" if hi_threats else "Low", "trend": [round(sum(rev[i - 2:i + 1]), 2) for i in range(5, 24, 3)] if HAS_S else []}, "facets": {"region": regions}, "drill_down_target": "D-revenue"}] +
                               [{"id": p_["account"], "cells": {"account": p_["account"], "revenue": {"v": p_["revenue_m"], "d": money(p_["revenue_m"])}, "growth": {"v": p_["revenue_m"] / p_["prev_revenue_m"] - 1, "d": spct(p_["revenue_m"] / p_["prev_revenue_m"] - 1)},
                                                                "pipeline": {"v": p_["pipeline_m"], "d": money(p_["pipeline_m"])}, "risk": p_["risk"], "trend": p_["series"]}, "facets": {"region": [p_["region"]]}, "drill_down_target": None} for p_ in B.get("peers", [])],
                       "source": src_bill},
          "opportunities": {"columns": [{"id": "name", "label": "Opportunity", "type": "text"}, {"id": "category", "label": "Category", "type": "text"}, {"id": "stage", "label": "Stage", "type": "text"},
                                        {"id": "value", "label": "Value", "type": "money"}, {"id": "prob", "label": "Probability", "type": "pct"}, {"id": "weighted", "label": "Weighted", "type": "money"},
                                        {"id": "competitor", "label": "Competitor", "type": "text"}, {"id": "close", "label": "Close", "type": "date"}, {"id": "owner", "label": "Owner", "type": "text"}, {"id": "region", "label": "Region", "type": "text"}],
                            "rows": [{"id": o["id"], "cells": {"name": o["label"], "category": o["category"], "stage": o["stage"], "value": {"v": o["value"], "d": o["display"]}, "prob": {"v": o["probability"], "d": o["probability_display"], "delta": o["delta_display"]},
                                                               "weighted": {"v": o["value"] * o["probability"], "d": o["weighted_display"]}, "competitor": o["competitor"] or "—", "close": o["close_date"], "owner": o["owner"], "region": o["region"]},
                                      "facets": o["facets"], "drill_down_target": o["drill_down_target"]} for o in opps], "source": OPPS[0]["source"]}}
# ---------------- drill graph ----------------
drill = {}
def node(id_, label, display, kind, children=(), evidence=(), links=None, text=None):
    drill[id_] = {"id": id_, "label": label, "display": display, "kind": kind, "children": list(children), "evidence": [e_ for e_ in evidence if e_], "links": links or {}, "text": text}
for o in opps:
    t = threat_by_comp.get(o["competitor"]); aid = f"ACT-{o['id']}" if any(x["id"] == f"ACT-{o['id']}" for x in ACTIONS) else (t and next((th["recommended_action_id"] for th in threads if th["competitor"] == t["competitor_id"] and th["recommended_action_id"]), None))
    node(f"D-opp-{o['id']}-ev", "Evidence", f"{len(o['evidence'])} items", "evidence", evidence=o["evidence"])
    sigs = [s["id"] for s in signals if o["id"] in s.get("facets", {}).get("opportunity", []) or (o["competitor"] and o["competitor"] in s.get("facets", {}).get("competitor", []))][:8]
    node(f"D-opp-{o['id']}-sig", "Signals", f"{len(sigs)} signals", "signals", links={"signals": sigs}, evidence=o["evidence"][:1])
    node(f"D-opp-{o['id']}-drv", "Business driver", o["driver"], "driver", evidence=[f"EV-{o['id']}"], text=f"Growth driver: {o['driver']}; incremental growth {o['growth_value_display']}")
    node(f"D-opp-{o['id']}-comp", "Competitive context", o["competitive_context"], "competitive", evidence=o["evidence"][1:4] or o["evidence"][:1], links={"threads": [th["id"] for th in threads if th["competitor"] == o["competitor"]]})
    node(f"D-opp-{o['id']}-act", "Recommended action", next((x["label"] for x in ACTIONS if x["id"] == aid), "No action proposed yet") if aid else "No action proposed yet", "action", evidence=[f"EV-{o['id']}"], links={"actions": [aid] if aid else []})
    node(o["drill_down_target"], o["label"], o["display"], "opportunity", [f"D-opp-{o['id']}-{k}" for k in ("ev", "sig", "drv", "comp", "act")], o["evidence"][:1], {"opportunity": o["id"]})
for d in drivers["children"]:
    node(d["drill_down_target"], d["label"], d["display"], "driver", [o["drill_down_target"] for o in opps if o["driver"] == d["label"]], [], {"facet": d["facet"]})
node("D-growth_potential", "Growth potential", money(gp), "metric", [d["drill_down_target"] for d in drivers["children"]], KPI["growth_potential"]["evidence"][:3])
for cat in CATS:
    node(f"D-cat-{cat}", cat, money(agg(lambda o: o["value_m"], lambda o, c=cat: o["category"] == c)), "category", [o["drill_down_target"] for o in opps if o["category"] == cat], [], {"facet": {"category": cat}})
node("D-pipeline", "Pipeline", money(pipe), "metric", [f"D-cat-{c}" for c in CATS if any(o["category"] == c for o in OPPS)], KPI["pipeline"]["evidence"][:3])
node("D-forecast", "Weighted forecast", money(fc), "metric", [o["drill_down_target"] for o in sorted(opps, key=lambda o: -o["value"] * o["probability"])], KPI["forecast"]["evidence"][:3], text=KPI["forecast"]["note"])
node("D-opportunity_value", "New opportunities", money(ov), "metric", [f"D-cat-{c}" for c in CATS if c != "Renewal" and any(o["category"] == c for o in OPPS)], KPI["opportunity_value"]["evidence"][:3])
node("D-risk_exposure", "Value at risk", money(rx), "metric", [o["drill_down_target"] for o in opps if contested(next(x for x in OPPS if x["id"] == o["id"]))], KPI["risk_exposure"]["evidence"][:3], text=KPI["risk_exposure"]["note"])
for c in landscape:
    node(c["drill_down_target"], c["label"], f"Threat {c['threat']}", "competitor", [o["drill_down_target"] for o in opps if o["competitor"] == c["label"]] + [f"D-thread-{t['id']}" for t in threads if t["competitor"] == c["label"]], c["evidence"][:3])
node("D-competitive_exposure", "Competitive exposure", pct(cx, 0), "metric", [c["drill_down_target"] for c in landscape if c["threat"] in ("High", "Medium")], KPI["competitive_exposure"]["evidence"][:3], text=KPI["competitive_exposure"]["note"])
qn = [f"D-q-{q['quarter']}" for q in Q[-4:]]
for q in Q[-4:]: node(f"D-q-{q['quarter']}", q["quarter"], money(q["revenue_m"]), "period", [], [f"EV-Q-{q['quarter']}"])
# drill nodes exist only for available metrics (unavailable KPIs carry no drill target)
if HAS_S: node("D-revenue", "Revenue (TTM)", money(ttm), "metric", qn, ["EV-SERIES"])
if HAS_Q: node("D-revenue_growth", "Revenue growth", spct(yoy_q), "metric", [f"D-q-{Q[-1]['quarter']}"], [f"EV-Q-{Q[-1]['quarter']}", f"EV-Q-{Q[-5]['quarter']}"], text="Latest quarter vs the same quarter a year earlier")
if CAN_FIN and HAS_Q: node("D-margin", "Account gross margin", pct(gm[-1]), "metric", qn, [f"EV-Q-{Q[-1]['quarter']}"])
for t in threads:
    node(t["drill_down_target"], t["label"], f"{t['momentum']} · risk {t['risk']}", "thread", [o["drill_down_target"] for o in opps if o["id"] in t["opportunities"]], t["evidence"], {"thread": t["id"]})
for r_ in risks: node(r_["drill_down_target"], r_["label"], r_["impact_display"], "risk", [], r_["evidence"], {"risk": r_["id"]}, text=f"Mitigation: {r_['mitigation']}")
for x in rels: node(x["drill_down_target"], f"{x['label']} · {x['role']}", x["strength"], "stakeholder", [o["drill_down_target"] for o in opps if o["id"] in x["opportunities"]], x["evidence"])
for c in changes: node(c["drill_down_target"], c["label"], c["display"], "change", [], c["evidence"])
# ---------------- filters ----------------
pools = opps + threads + risks + rels + changes + ACTIONS + signals
filters = []
for dim_, lab in [("competitor", "Competitor"), ("driver", "Growth driver"), ("category", "Opportunity type"), ("region", "Region"), ("domain", "Domain"), ("stakeholder", "Stakeholder")]:
    vals = sorted({v for x in pools for v in (x.get("facets") or {}).get(dim_, [])} - {"None"})
    vl = [{"value": v, "label": next((f"{x['name']} ({x['role']})" for x in EXECS if x["id"] == v), v), "count": sum(1 for x in pools if v in (x.get("facets") or {}).get(dim_, []))} for v in vals]
    filters.append({"id": f"f-{dim_}", "dimension": dim_, "label": lab, "values": vl})
# ---------------- layout (persona) ----------------
W_ = {"kpis": ("kpi_strip", "Executive KPIs", 12), "state": ("narrative", "State of the business", 12), "changes": ("change_list", "What changed", 12),
      "trend": ("trend_chart", "Performance trend", 8), "drivers": ("driver_tree", "What is driving growth", 4), "radar": ("opportunity_radar", "Opportunity radar", 7),
      "risk_matrix": ("risk_matrix", "Strategic risk", 5), "competitors": ("competitor_landscape", "Competitive landscape", 12), "threads": ("thread_list", "Competitive threads", 12),
      "financial_summary": ("financial_panel", "Financial intelligence", 12), "marketing_summary": ("marketing_panel", "Marketing signals", 12), "relationships": ("relationship_map", "Executive relationship map", 12),
      "swot": ("swot", "Dynamic SWOT", 12), "health": ("health", "Account health", 12), "actions": ("action_list", "Recommended actions", 12), "scenario_lab": ("scenario_lab", "Scenario lab", 12),
      "comparison": ("comparison", "Comparison", 12), "accounts_table": ("table", "Accounts", 12), "pipeline_table": ("table", "Opportunities", 12), "insights": ("insight_list", "Insights", 12),
      "decisions": ("decision_list", "Decisions", 12), "operations": ("metric_grid", "Operations", 12), "market": ("event_list", "Market and customer events", 12), "signals": ("signal_list", "Signals", 12)}
PAIRS = {("trend", "drivers"), ("radar", "risk_matrix")}
def pack(ids):
    out, i = [], 0; ids = [x for x in ids if x in W_ and not (x == "marketing_summary" and not marketing) and not (x == "financial_summary" and not (financial["public"] or financial["account"]))]
    # pull a widget's partner next to it so every row sums to 12 columns
    for a_, b_ in PAIRS:
        if a_ in ids and b_ in ids and ids.index(b_) != ids.index(a_) + 1:
            ids.remove(b_); ids.insert(ids.index(a_) + 1, b_)
    while i < len(ids):
        w = ids[i]; t_, ti, sp = W_[w]
        if sp < 12 and i + 1 < len(ids) and (w, ids[i + 1]) in PAIRS:
            out.append({"id": w, "type": t_, "title": ti, "span": sp}); n_ = ids[i + 1]; out.append({"id": n_, "type": W_[n_][0], "title": W_[n_][1], "span": 12 - sp}); i += 2; continue
        out.append({"id": w, "type": t_, "title": ti, "span": 12}); i += 1
    return out
VIEWS = {"overview": P["overview"], "growth": ["trend", "drivers", "radar", "risk_matrix", "pipeline_table", "insights"], "accounts": ["accounts_table", "health", "comparison"],
         "pipeline": ["pipeline_table", "radar", "risk_matrix", "trend"], "customers": ["health", "relationships", "swot"], "competition": ["competitors", "threads", "radar", "risk_matrix"],
         "market": ["market", "insights", "signals"], "financial": ["financial_summary", "trend", "insights"], "marketing": ["marketing_summary", "signals"],
         "operations": ["operations", "health", "changes"], "decisions": ["decisions", "scenario_lab", "comparison"], "actions": ["actions"]}
TABS = {"overview": "Overview", "growth": "Growth", "accounts": "Accounts", "pipeline": "Pipeline", "customers": "Customers", "competition": "Competition", "market": "Market",
        "financial": "Financial", "marketing": "Marketing", "operations": "Operations", "decisions": "Decisions", "actions": "Actions"}
hidden = []
if not CAN_MKT: hidden.append("marketing")
nav = [{"id": k, "label": TABS[k]} for k in TABS if k in P["tabs"] and k not in hidden]
# Every view the ROLE may see is included (the persona only chooses which tabs to show), so a persona switch in the UI never
# lands on an empty tab; views the role may not see are never emitted.
layout = {"grid_columns": 12, "breakpoints": [1280, 1440, 1600, 1920], "views": {k: pack(v) for k, v in VIEWS.items() if k not in hidden}}
# Persona layouts: presentation only (tab order, overview composition, KPI order). Data and permissions are the same for every
# persona because they follow the ROLE, so switching persona in the UI never exposes restricted data.
persona_layouts = {k: {"label": v["label"], "altitude": v["altitude"], "navigation": [{"id": t_, "label": TABS[t_]} for t_ in TABS if t_ in v["tabs"] and t_ not in hidden],
                       "overview": pack(v["overview"]), "kpis": [x for x in v["kpis"] if x in KPI], "emphasis": v.get("emphasis", [])} for k, v in PERS.items()}
queries = [{"id": "Q1", "question": "What changed in the last 30 days?", "route": "business-orchestrator", "ui_target": {"view": "overview", "focus": "changes"}},
           {"id": "Q2", "question": "Why is competitive risk increasing?", "route": "business-orchestrator", "ui_target": {"view": "competition", "focus": "threads"}},
           {"id": "Q3", "question": "Which competitor is gaining ground?", "route": "business-orchestrator", "ui_target": {"view": "competition", "focus": "competitors"}},
           {"id": "Q4", "question": "Show me only financial signals.", "route": "business-orchestrator", "ui_target": {"filter": {"domain": "financial"}}},
           {"id": "Q5", "question": "Find my biggest opportunities.", "route": "business-orchestrator", "ui_target": {"view": "growth", "focus": "radar"}},
           {"id": "Q6", "question": "Where is marketing creating pipeline?", "route": "business-orchestrator", "ui_target": {"view": "marketing", "focus": "marketing_summary"} if CAN_MKT else None},
           {"id": "Q7", "question": "What should I do next?", "route": "business-orchestrator", "ui_target": {"view": "actions", "focus": "actions"}},
           {"id": "Q8", "question": f"What happens if {renew['competitor'] if renew else 'the competitor'} wins the renewal?", "route": "business-orchestrator", "ui_target": {"view": "decisions", "focus": "scenario_lab"}},
           {"id": "Q9", "question": "Why did growth change?", "route": "business-orchestrator", "ui_target": {"view": "overview", "focus": "trend"}},
           {"id": "Q10", "question": "Which accounts are warming?", "route": "business-orchestrator", "ui_target": {"view": "marketing", "focus": "marketing_summary"} if CAN_MKT else None}]
# Persona layouts: presentation only (same data; role restrictions already applied above)
persona_layouts = {}
for pk, pc in PERS.items():
    pnav = [{"id": k, "label": TABS[k]} for k in TABS if k in pc["tabs"] and k not in hidden]
    pviews = {k: pack(pc["overview"] if k == "overview" else v) for k, v in VIEWS.items() if any(n["id"] == k for n in pnav)}
    persona_layouts[pk] = {"label": pc["label"], "altitude": pc["altitude"], "navigation": pnav, "kpis": [k for k in pc["kpis"] if k in KPI], "views": pviews, "emphasis": pc["emphasis"]}
kpi_conf = [m["confidence"] for m in metrics if m.get("confidence") is not None]   # unavailable metrics do not count
ev_dates = [e_["date"] for e_ in EVID.values() if e_["date"]]
stale = sorted({e_["source"] for e_ in EVID.values() if e_["date"] and (datetime.fromisoformat(ASOF) - datetime.fromisoformat(e_["date"][:10])).days > 180})
C = {"contract_version": "1.0",
     "dashboard": {"id": "enterprise-growth-command-center", "name": "Enterprise Growth Command Center", "persona": a.persona, "persona_label": P["label"], "altitude": P["altitude"], "scope": "account",
                   "entity_id": E["id"], "entity_name": ENAME, "entity_segment": E["segment"], "period": E["period"], "last_updated": datetime.now().isoformat(timespec="seconds"),
                   "data_freshness": {"as_of": ASOF, "oldest_source_date": min(ev_dates) if ev_dates else None, "stale_sources_over_180_days": stale},
                   "overall_confidence": round(statistics.mean(kpi_conf), 2) if kpi_conf else 0.0, "metrics_available": f"{len(kpi_conf)} of {len(metrics)}", "data_mode": MODE, "data_notice": B.get("data_notice"), "tenant": E.get("tenant"), "role": a.role},
     "navigation": nav, "layout": layout, "persona_layouts": persona_layouts, "filters": filters, "metrics": metrics, "narrative": narrative, "changes": changes, "trends": trends, "insights": insights, "signals": signals,
     "drivers": drivers, "opportunities": opps, "risks": risks, "financial": financial, "marketing": marketing, "competition": {"landscape": landscape}, "competitive_threads": threads,
     "relationships": rels, "swot": swot, "health": health, "scenarios": scen, "actions": ACTIONS, "comparisons": comparisons, "comparisons_unavailable": comparisons_unavailable, "tables": tables, "decisions": B.get("decisions", []),
     "operations": [dict(o, display=pct(o["value"]) if o["unit"] == "ratio" else f"{o['value']:g}", previous_display=pct(o["previous"]) if o["unit"] == "ratio" else f"{o['previous']:g}",
                         delta_display=spp(o["value"] - o["previous"]) if o["unit"] == "ratio" else f"{o['value'] - o['previous']:+g}",
                         sentiment=senti(o["value"] - o["previous"], not o.get("higher_is_worse")), evidence=[f"EV-OPS-{o['id']}"]) for o in B.get("operations", [])],
     "market": [{"id": f"MKT-{e_['type']}", "label": e_["text"], "date": e_.get("date"), "source": e_["source"], "evidence": [f"EV-MKT-{e_['type']}"], "claim_type": "FACT", "data_mode": "public"} for e_ in B.get("market_events", [])],
     "persona_layouts": persona_layouts, "drill": drill, "queries": queries, "evidence": list(EVID.values()),
     "state_defaults": {"persona": a.persona, "view": "overview", "time_range": "24m", "filters": {}, "theme": "light"},
     "permissions": {"role": a.role, "data_classes": sorted(DATA), "hidden_tabs": hidden, "restricted": restricted},
     "provenance": {"builder": "dashboard_builder.py (T0)", "provider": B["provider"], "engines": B.get("engines_run", []), "generated_at": datetime.now().isoformat(timespec="seconds"),
                    "schema": "schemas/dashboard.schema.json", "anomaly_rule": "deviation from trailing 6-month linear trend ≥ 7% and ≥ 3× residual scale"}}
# ---------------- V8: starter prompts (Growth Discovery) — context-aware suggestions and Explore capabilities ----------------
UI_TARGET = {"threads": {"view": "competition", "focus": "threads"}, "competition": {"view": "competition", "focus": "competitors"}, "financial": {"view": "financial", "focus": "financial_summary"},
             "marketing": {"view": "marketing", "focus": "marketing_summary"}, "scenario": {"view": "decisions", "focus": "scenario_lab"}, "decision": {"view": "decisions", "focus": "decisions"},
             "actions": {"view": "actions", "focus": "actions"}, "opportunities": {"view": "growth", "focus": "radar"}, "forecast": {"view": "pipeline", "focus": "pipeline_table"},
             "deal": {"view": "pipeline", "focus": "radar"}, "relationships": {"view": "customers", "focus": "relationships"}, "account": {"view": "overview", "focus": "changes"},
             "bi": {"view": "overview", "focus": "trend"}, "customer-growth": {"view": "customers", "focus": "health"}, "renewals": {"view": "customers", "focus": "health"}, "executive": {"view": "overview", "focus": "state"}}
PE = find_up("skills/growth-discovery/scripts/prompt_engine.py")
if PE:
    import subprocess
    json.dump(C, open(a.out, "w"), default=str)
    def pe(*args):
        r = subprocess.run([sys.executable, PE, *args], capture_output=True, text=True); return json.loads(r.stdout) if r.stdout.strip().startswith("{") else {}
    pers_pe = a.persona if a.persona in ("investor", "ceo", "cfo", "coo", "cro", "growth_ops", "sales_head", "sales_director", "ae") else None
    rec = pe("recommend", "--contract", a.out, "--limit", "6", *(["--persona", pers_pe] if pers_pe else []))
    nav_ids = {n["id"] for n in nav}
    def ut(cid): x = UI_TARGET.get(cid); return x if x and x.get("view") in nav_ids else None
    if rec.get("prompts"):
        C["queries"] = [{"id": f"Q{i + 1}", "question": p_["prompt"], "route": "business-orchestrator", "capability": p_["capability"], "capability_id": p_["_route"]["capability_id"],
                         "tier": p_.get("tier", "primary"), "why": p_.get("why"), "ui_target": ut(p_["_route"]["capability_id"])} for i, p_ in enumerate(rec["prompts"])]
    lead_comp = next((t_["competitor"] for t_ in threads if t_["status"] == "active" and t_["risk"] == "High" and t_["thread_type"] != "displacement_opportunity"), None)
    CTXA = ["--account", ENAME] + (["--competitor", lead_comp] if lead_comp else [])      # known context is inserted, never retyped
    hm = pe("home", *CTXA, *(["--persona", pers_pe] if pers_pe else []))
    explore = [{"category": cat["category"], "capabilities": list(cat["capabilities"])} for cat in hm.get("explore", [])]
    menus = {}
    catdir = os.path.join(os.path.dirname(PE), "..", "references", "starter-prompts")
    for f in sorted(os.listdir(catdir)):
        if f.startswith("_"): continue
        cid = f[:-5]; mres = pe("menu", "--capability", cid, *CTXA, *(["--persona", pers_pe] if pers_pe else []))
        if mres.get("prompts"): menus[mres["capability"]] = {"capability_id": cid, "description": mres["description"], "prompts": [x["prompt"] for x in mres["prompts"]]}
    C["discovery"] = {"title": hm.get("title"), "prompts": [{"prompt": x["prompt"], "capability": x["capability"], "capability_id": x["_route"]["capability_id"]} for x in hm.get("prompts", [])],
                      "explore": [{"category": e["category"], "capabilities": [c_ for c_ in e["capabilities"] if c_ in menus]} for e in explore], "menus": menus,
                      "source": "growth-discovery starter-prompt catalog (business language; routes through the Business Orchestrator)"}
json.dump(C, open(a.out, "w"), indent=1, default=str)
res = {"contract": a.out, "persona": a.persona, "role": a.role, "metrics": len(metrics), "changes": len(changes), "opportunities": len(opps), "risks": len(risks), "threads": len(threads),
       "actions": len(ACTIONS), "evidence": len(EVID), "drill_nodes": len(drill), "signals": len(signals), "anomalies": len(anomalies), "restricted": restricted}
if a.validate:
    import jsonschema
    sch = json.load(open(find_up("schemas/dashboard.schema.json")))
    errs = sorted(jsonschema.Draft202012Validator(sch).iter_errors(json.loads(json.dumps(C, default=str))), key=lambda e: list(e.path))
    res["schema_errors"] = [f"{'/'.join(map(str, e.path))}: {e.message[:120]}" for e in errs[:15]]; res["schema_valid"] = not errs
print(json.dumps(res, indent=1))
