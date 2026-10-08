#!/usr/bin/env python3
"""
demo_provider.py: DEMO data provider for the Dashboard Intelligence layer.

Produces an intelligence BUNDLE (the same shape production_provider.py produces) by generating demo inputs and
running the REAL V7.1 engines on them: financial_intel.py, marketing_signals.py, competitive_threads.py,
cross_domain_correlator.py, domain_delta.py. dashboard_builder.py then turns the bundle into a Dashboard Contract.

Labelling: every demo record's source starts with "DEMO DATA — NOT REAL CUSTOMER DATA". The only real-world
claims about the demo entity are published financial figures and events (references/demo/*_PUBLIC.json), each with
its citation. Demo relationship data uses generic names (Competitor X, Contact A) and makes no claims about the
entity's programs or people.

Contents: 1 enterprise account (+2 peer accounts for comparison) · 5 competitors · 10 opportunities · 15 executives ·
20 marketing signals (+8 peer) · 15 financial signals (5 public + 10 account-economics) · 8 competitive threads ·
≥20 account changes (via domain_delta) · 24-month performance series.

USAGE: demo_provider.py --entity Sanofi --asof 2026-09-30 [--memory-db mem.db] --out bundle.json
"""
import sys
import argparse, json, os, subprocess, tempfile, math, shutil
from datetime import date
HERE = os.path.dirname(os.path.abspath(__file__)); REF = os.path.join(os.path.dirname(HERE), "references", "demo")
DEMO = "DEMO DATA — NOT REAL CUSTOMER DATA"
ap = argparse.ArgumentParser(); ap.add_argument("--entity", default="Sanofi"); ap.add_argument("--asof", default="2026-09-30")
ap.add_argument("--memory-db"); ap.add_argument("--out", required=True); a = ap.parse_args()
E, ASOF = a.entity, a.asof
T = tempfile.mkdtemp(); MEM = a.memory_db or f"{T}/mem.db"
def run(script, *args):
    r = subprocess.run([sys.executable, os.path.join(HERE, script), *map(str, args)], capture_output=True, text=True)
    if r.returncode not in (0, 1) or not r.stdout.strip().startswith(("{", "[")): raise SystemExit(f"{script} failed: {r.stderr[-400:]}")
    return json.loads(r.stdout)
def W(name, obj): p = f"{T}/{name}"; json.dump(obj, open(p, "w"), default=str); return p
src = lambda what: f"{DEMO} ({what})"
# ---------------- performance series (24 months, $M, our revenue from the account) ----------------
months = [f"{2024 + (9 + i) // 12}-{(9 + i) % 12 + 1:02d}" for i in range(24)]            # 2024-10 … 2026-09
rev = [round(6.05 * (1.0098 ** i) * (1 + 0.035 * math.sin(i / 1.9)), 3) for i in range(24)]
rev[20] = round(rev[20] * 0.86, 3)                                                            # a genuine dip in 2026-06 (anomaly test)
bookings = [round(r * (1.05 + 0.25 * math.cos(i / 2.3)), 3) for i, r in enumerate(rev)]
pipeline = [round(48 + i * 0.8 + 3 * math.sin(i / 2.0), 2) for i in range(24)]; pipeline[-1] = 66.1
margin = [round(0.352 - 0.0012 * i + 0.004 * math.sin(i / 3), 4) for i in range(24)]
target = [round(6.2 * (1.012 ** i), 3) for i in range(24)]
fc_months = ["2026-10", "2026-11", "2026-12"]; fc = [round(rev[-1] * (1.01 ** (k + 1)), 3) for k in range(3)]
prior_fc = [round(x * f, 3) for x, f in zip(rev[-3:], (1.03, 1.18, 1.02))]           # forecast made at the start of Q3-26
series = {"prior_forecast": {"months": months[-3:], "values": prior_fc, "source": src("finance forecast (start of Q3-26)")}, "months": months, "revenue": rev, "bookings": bookings, "pipeline": pipeline, "margin": margin, "target": target,
          "forecast": {"months": fc_months, "values": fc, "source": src("finance forecast")}, "source": src("billing and CRM monthly")}
# Annotations carry their own evidence (or reference a signal id); the builder registers them generically.
annotations = [{"t": "2026-01", "label": f"{E} FY2025 results published", "evidence": {"id": "EV-ANN-2026-01", "source": "Sanofi press release, 29 Jan 2026 (Q4 & FY2025 results)", "date": "2026-01-29", "observation": f"{E} published FY2025 results", "data_mode": "public"}},
               {"t": "2026-06", "label": "Revenue dip: delayed milestone billing", "evidence": {"id": "EV-ANN-2026-06", "source": src("billing"), "date": "2026-06-30", "observation": "Milestone billing moved to the following month", "data_mode": "demo"}},
               {"t": "2026-08", "label": "Competitor X joins the renewal RFP", "signal_id": "CS-13"}]
# Scenario definitions are DATA from the provider (which deals, contract terms, dependencies); the builder only computes them.
scenario_specs = [{"type": "opportunity_loss", "opportunity": "OPP-01", "term_years": 3, "dependent_opportunities": ["OPP-03"], "dependency_note": "The procure-to-pay expansion depends on the renewal"},
                  {"type": "opportunity_win", "opportunity": "OPP-02", "term_years": 2},
                  {"type": "slip", "top_n": 2, "days": 90}]
# ---------------- opportunities (10) ----------------
O = [  # id, name, category, value $M, probability, strategic impact, stage, competitor, driver, growth value, region, product, close, owner
 ("OPP-01", "Finance operations renewal", "Renewal", 25.0, .70, .95, "Negotiation", "Competitor X", "Pricing", 2.5, "Europe", "Finance & Accounting", "2026-12-15", "Rep 1"),
 ("OPP-02", "AI transformation for operations", "Transformation", 8.0, .45, .90, "Solutioning", "Competitor Z", "Expansion", 8.0, "North America", "AI Services", "2027-03-31", "Rep 2"),
 ("OPP-03", "Procure-to-pay expansion to Europe", "Expansion", 6.5, .60, .70, "Proposal", None, "Expansion", 6.5, "Europe", "Finance & Accounting", "2026-12-31", "Rep 1"),
 ("OPP-04", "Analytics platform displacement", "Displacement", 5.2, .35, .75, "Qualification", "Competitor Y", "New Business", 5.2, "North America", "Analytics", "2027-02-28", "Rep 3"),
 ("OPP-05", "Regulatory document automation", "New Business", 4.8, .30, .60, "Discovery", "Competitor Q", "New Business", 4.8, "Europe", "AI Services", "2027-04-30", "Rep 2"),
 ("OPP-06", "Commercial data services", "Cross-sell", 3.6, .55, .50, "Proposal", None, "Cross-Sell", 3.6, "North America", "Analytics", "2026-11-30", "Rep 3"),
 ("OPP-07", "Supply chain control tower", "Transformation", 3.5, .25, .65, "Discovery", "Competitor Z", "Expansion", 3.5, "APAC", "Supply Chain", "2027-05-31", "Rep 4"),
 ("OPP-08", "HR services cross-sell", "Cross-sell", 2.9, .50, .40, "Qualification", "Competitor R", "Cross-Sell", 2.9, "Europe", "HR Services", "2027-01-31", "Rep 4"),
 ("OPP-09", "Launch analytics capacity", "New Business", 4.4, .40, .55, "Discovery", None, "Market Growth", 4.4, "APAC", "Analytics", "2027-03-31", "Rep 3"),
 ("OPP-10", "Cybersecurity managed service", "New Business", 2.2, .30, .35, "Discovery", "Competitor Q", "New Business", 2.2, "North America", "Cybersecurity", "2027-06-30", "Rep 2")]
opps = [dict(zip(["id", "name", "category", "value_m", "probability", "strategic_impact", "stage", "competitor", "driver", "growth_value_m", "region", "product", "close_date", "owner"], o), source=src("CRM opportunity")) for o in O]
prev_prob = {"OPP-01": .80, "OPP-02": .35, "OPP-04": .30, "OPP-07": .30}                   # a month ago (for deltas)
for o in opps: o["previous_probability"] = prev_prob.get(o["id"], o["probability"])
# ---------------- executives (15) ----------------
X = [("C-A", "Contact A", "CIO", .95, "Strong", "up", "2026-09-24", True, "Low", ["OPP-02", "OPP-07"]),
     ("C-B", "Contact B", "CFO", .90, "Medium", "flat", "2026-08-12", False, "Medium", ["OPP-01"]),
     ("C-C", "Contact C", "Chief Procurement Officer", .80, "Weak", "down", "2026-06-30", False, "High", ["OPP-01", "OPP-03"]),
     ("C-D", "Contact D", "VP Digital Operations", .75, "Medium", "down", "2026-09-12", False, "High", ["OPP-01", "OPP-02"]),
     ("C-E", "Contact E", "Head of Procurement", .60, "Weak", "flat", "2026-07-20", False, "Medium", ["OPP-01"]),
     ("C-F", "Contact F", "VP Finance Transformation", .70, "Strong", "up", "2026-09-18", True, "Low", ["OPP-03", "OPP-01"]),
     ("C-G", "Contact G", "Head of AI", .65, "Medium", "up", "2026-09-05", False, "Low", ["OPP-02", "OPP-05"]),
     ("C-H", "Contact H", "Global Head of R&D Operations", .70, "Weak", "flat", "2026-05-14", False, "Medium", ["OPP-05"]),
     ("C-I", "Contact I", "VP IT Infrastructure", .55, "Medium", "flat", "2026-08-28", False, "Low", ["OPP-10"]),
     ("C-J", "Contact J", "Director of Analytics", .50, "Strong", "up", "2026-09-21", True, "Low", ["OPP-04", "OPP-06"]),
     ("C-K", "Contact K", "Head of Commercial Operations", .60, "Medium", "up", "2026-09-02", False, "Low", ["OPP-06", "OPP-09"]),
     ("C-L", "Contact L", "VP HR Operations", .45, "Weak", "down", "2026-06-10", False, "Medium", ["OPP-08"]),
     ("C-M", "Contact M", "Head of Supply Chain Digital", .55, "Medium", "flat", "2026-08-15", False, "Low", ["OPP-07"]),
     ("C-N", "Contact N", "CISO", .60, "Weak", "flat", "2026-04-22", False, "Medium", ["OPP-10"]),
     ("C-O", "Contact O", "Chief Data Officer", .80, "Medium", "up", "2026-09-10", False, "Low", ["OPP-02", "OPP-04", "OPP-09"])]
execs = [dict(zip(["id", "name", "role", "influence", "strength", "trend", "last_interaction", "champion", "risk", "opportunities"], x), source=src("CRM contact and activity log")) for x in X]
contacts = [{"contact_id": x["id"], "role": x["role"]} for x in execs]
# ---------------- marketing signals (20 for the account + 8 for peers) → marketing_signals.py ----------------
M = [("2026-04-14", "email_open", "C-E", "CMP-FIN", "finance transformation"), ("2026-05-06", "website_visit", None, None, None),
     ("2026-05-28", "email_click", "C-B", "CMP-FIN", "finance transformation"), ("2026-06-19", "content_download", "C-L", "CMP-HR", "hr services"),
     ("2026-07-02", "webinar_attend", "C-G", "CMP-AI", "ai automation"), ("2026-07-09", "content_download", "C-D", "CMP-AI", "ai automation"),
     ("2026-07-16", "email_click", "C-O", "CMP-DATA", "data platform"), ("2026-07-24", "event_attend", "C-F", "CMP-FIN", "finance transformation"),
     ("2026-08-03", "exec_briefing_attend", "C-A", "CMP-AI", "ai automation"), ("2026-08-07", "pricing_page_visit", "C-G", None, "ai automation"),
     ("2026-08-13", "third_party_intent", None, None, "ai automation"), ("2026-08-19", "webinar_attend", "C-O", "CMP-DATA", "data platform"),
     ("2026-08-26", "content_download", "C-J", "CMP-DATA", "data platform"), ("2026-09-01", "third_party_intent", None, None, "finance transformation"),
     ("2026-09-04", "demo_request", "C-G", "CMP-AI", "ai automation"), ("2026-09-09", "exec_meeting", "C-A", None, "ai automation"),
     ("2026-09-15", "event_attend", "C-K", "CMP-DATA", "data platform"), ("2026-09-18", "pricing_page_visit", "C-F", None, "finance transformation"),
     ("2026-09-22", "competitor_comparison_view", None, None, "ai automation"), ("2026-09-26", "unsubscribe", "C-L", "CMP-HR", None)]
msig = [{"signal_id": f"MS-{i + 1:02d}", "account_id": E, "occurred_at": d, "type": t, "contact_id": c, "campaign_id": cmp, "topic": tp, "source": src("marketing automation")} for i, (d, t, c, cmp, tp) in enumerate(M)]
for i, (acc, d, t) in enumerate([("Account B", "2026-04-20", "webinar_attend"), ("Account B", "2026-05-15", "content_download"), ("Account B", "2026-06-02", "pricing_page_visit"),
                                 ("Account B", "2026-08-30", "email_open"), ("Account C", "2026-07-11", "email_click"), ("Account C", "2026-08-21", "webinar_attend"),
                                 ("Account C", "2026-09-08", "demo_request"), ("Account C", "2026-09-19", "content_download")]):
    msig.append({"signal_id": f"MP-{i + 1:02d}", "account_id": acc, "occurred_at": d, "type": t, "source": src("marketing automation")})
camps = [{"campaign_id": "CMP-AI", "name": "AI in operations briefing series"}, {"campaign_id": "CMP-FIN", "name": "Finance transformation summit"},
         {"campaign_id": "CMP-DATA", "name": "Data platform webinar series"}, {"campaign_id": "CMP-HR", "name": "HR services nurture"}]
mopps = [{"opportunity_id": o["id"], "account_id": E, "created_at": c, "amount": o["value_m"] * 1e6} for o, c in zip(opps, ["2026-03-01", "2026-09-10", "2026-08-20", "2026-09-01", "2026-09-25", "2026-09-20", "2026-07-15", "2026-06-15", "2026-09-28", "2026-08-01"])]
for o, m_ in zip(opps, mopps): o["created_at"] = m_["created_at"]
mk = run("marketing_signals.py", "--signals", W("ms.json", msig), "--contacts", W("c.json", contacts), "--opportunities", W("mo.json", mopps), "--campaigns", W("cp.json", camps),
         "--asof", ASOF, "--memory-db", MEM, "--out", f"{T}/mk.json")
# ---------------- public financials (real, cited) → financial_intel.py ----------------
fi = run("financial_intel.py", "--facts", os.path.join(REF, "sanofi_financials_PUBLIC.json"), "--events", os.path.join(REF, "sanofi_events_PUBLIC.json"),
         "--entity", E, "--public", "--memory-db", MEM, "--out", f"{T}/fi.json") if E == "Sanofi" else None
# ---------------- account economics (demo, quarterly) ----------------
quarters = []
for q in range(8):
    ms = slice(q * 3, q * 3 + 3); r = sum(rev[ms])
    gm = sum(margin[ms]) / 3
    quarters.append({"quarter": ["Q4-24", "Q1-25", "Q2-25", "Q3-25", "Q4-25", "Q1-26", "Q2-26", "Q3-26"][q], "revenue_m": round(r, 3), "gross_profit_m": round(r * gm, 3),
                     "cost_to_serve_m": round(r * (0.118 + 0.004 * q), 3), "accounts_receivable_m": round(r / 3 * (1.55 + 0.05 * q), 3), "bookings_m": round(sum(bookings[ms]), 3),
                     "source": src("ERP account P&L")})
# ---------------- competitive signals → competitive_threads.py (8 threads, 5 competitors) ----------------
def cs(i, d, comp, kind, text, **k): return dict({"signal_id": f"CS-{i:02d}", "account_id": E, "competitor_id": comp, "observed_at": d, "kind": kind, "text": text, "source": src(k.pop("s", "CRM and call notes"))}, **k)
S1 = [cs(1, "2025-10-02", "Competitor Y", "competitor_exec_meeting", "Competitor Y met the analytics leadership", stakeholder_id="C-J"),
      cs(2, "2025-11-10", "Competitor Y", "competitor_pilot", "Competitor Y proposed an analytics pilot", opportunity_id="OPP-04"),
      cs(3, "2025-08-01", "Competitor R", "competitor_mention", "Competitor R named in an HR services review", stakeholder_id="C-L"),
      cs(4, "2025-09-15", "Competitor R", "competitor_exec_meeting", "Competitor R met HR operations", stakeholder_id="C-L"),
      cs(5, "2026-02-10", "Competitor Q", "competitor_delivery_issue", "Customer escalated Competitor Q document-processing backlog", s="customer QBR")]
S2 = [cs(10, "2026-05-08", "Competitor X", "competitor_mention", "Competitor X mentioned in a finance operations review", stakeholder_id="C-E"),
      cs(11, "2026-06-11", "Competitor X", "competitor_mention", "Customer finance team attended a Competitor X webinar", s="event list"),
      cs(12, "2026-07-14", "Competitor X", "competitor_exec_meeting", "Competitor X met the CFO office", stakeholder_id="C-B"),
      cs(13, "2026-08-04", "Competitor X", "rfp_participation", "Competitor X invited to the finance operations renewal RFP", opportunity_id="OPP-01", s="RFP distribution list"),
      cs(14, "2026-08-21", "Competitor X", "pricing_undercut", "Procurement cited a lower Competitor X rate card", stakeholder_id="C-C", opportunity_id="OPP-01"),
      cs(15, "2026-09-12", "Competitor X", "champion_weakening", "VP Digital Operations less engaged with our team", stakeholder_id="C-D", relationship_signal="REL-01"),
      cs(16, "2026-09-23", "Competitor X", "competitor_exec_meeting", "Competitor X executive engagement with the CPO", stakeholder_id="C-C"),
      cs(17, "2026-08-25", "Competitor Y", "competitor_delivery_issue", "Customer escalated Competitor Y analytics delivery delays", opportunity_id="OPP-04", s="customer QBR"),
      cs(18, "2026-09-17", "Competitor Y", "competitor_delivery_issue", "Second escalation on Competitor Y data quality", s="customer QBR"),
      cs(19, "2026-06-05", "Competitor Z", "competitor_exec_meeting", "Competitor Z briefed the Head of AI", stakeholder_id="C-G", opportunity_id="OPP-02"),
      cs(20, "2026-08-18", "Competitor Z", "competitor_pilot", "Competitor Z offered a free AI pilot", opportunity_id="OPP-02"),
      cs(21, "2026-09-19", "Competitor Z", "pricing_undercut", "Competitor Z discounted the control-tower proposal", opportunity_id="OPP-07"),
      cs(22, "2026-07-06", "Competitor Q", "competitor_mention", "Competitor Q named for regulatory automation", opportunity_id="OPP-05"),
      cs(23, "2026-09-03", "Competitor Q", "competitor_exec_meeting", "Competitor Q met R&D operations", stakeholder_id="C-H", opportunity_id="OPP-05"),
      cs(24, "2026-09-25", "Competitor Q", "customer_positive_on_us", "R&D operations praised our regulatory automation demo"),
      cs(25, "2026-09-02", "Competitor R", "competitor_exit", "Competitor R exiting the HR services line in the region", s="market news summary")]
g1 = run("competitive_threads.py", MEM, "ingest", W("s1.json", S1), "--asof", ASOF)
yt = next(r["thread_id"] for r in g1 if r["signal"] == "CS-01")
run("competitive_threads.py", MEM, "outcome", yt, "--outcome", "won", "--date", "2025-12-20", "--evidence", src("award letter"))
g2 = run("competitive_threads.py", MEM, "ingest", W("s2.json", S2), "--asof", ASOF)
threads = run("competitive_threads.py", MEM, "query", "--account", E)
resolved = [t for t in threads if t["status"] == "resolved"]
# ---------------- relationship signals ----------------
rel = [{"signal_id": "REL-01", "account_id": E, "kind": "champion_weakening", "stakeholder": "C-D", "observed_at": "2026-09-12", "source": src("relationship review")},
       {"signal_id": "REL-02", "account_id": E, "kind": "exec_access_gained", "stakeholder": "C-A", "observed_at": "2026-09-09", "source": src("executive meeting log")},
       {"signal_id": "REL-03", "account_id": E, "kind": "sponsor_strengthening", "stakeholder": "C-F", "observed_at": "2026-09-18", "source": src("relationship review")}]
inits = [{"initiative_id": "INI-AI", "account_id": E, "topic": "ai automation", "text": "Customer AI-in-operations program discussed in the QBR", "source": src("QBR notes"), "source_date": "2026-08-05"}]
cd = run("cross_domain_correlator.py", "--account", E, "--marketing", f"{T}/mk.json", *(["--financial", f"{T}/fi.json"] if fi else []), "--threads", W("th.json", threads),
         "--relationship", W("rel.json", rel), "--initiatives", W("ini.json", inits), "--memory-db", MEM, "--asof", ASOF, "--out", f"{T}/cd.json")
# ---------------- snapshots → domain_delta.py (What changed) ----------------
def v(x, s, d, **k): return dict({"value": x, "source": s, "as_of": d}, **k)
# Snapshot values are DERIVED from the same series and quarters the builder uses, so every widget agrees.
ttm_now, ttm_prev = round(sum(rev[-12:]), 2), round(sum(rev[-13:-1]), 2)
qd = lambda q: round(q["accounts_receivable_m"] / q["revenue_m"] * 91, 1)
qc = lambda q: round(q["cost_to_serve_m"] / q["revenue_m"], 4)
PD, CD_ = "2026-08-31", "2026-09-30"
mk_prev = run("marketing_signals.py", "--signals", f"{T}/ms.json", "--contacts", f"{T}/c.json", "--asof", PD)          # marketing as of the previous snapshot
mu_now, mu_prev = mk["units"][E], mk_prev["units"][E]
TP = f"{T}/prev_threads.db"                                                                                      # competitive state as of the previous snapshot
run("competitive_threads.py", TP, "ingest", W("s1p.json", [s for s in S1 if s["observed_at"] <= PD]), "--asof", PD)
run("competitive_threads.py", TP, "outcome", run("competitive_threads.py", TP, "query", "--competitor", "Competitor Y")[0]["thread_id"], "--outcome", "won", "--date", "2025-12-20", "--evidence", src("award letter"))
run("competitive_threads.py", TP, "ingest", W("s2p.json", [s for s in S2 if s["observed_at"] <= PD]), "--asof", PD)
thr_prev = run("competitive_threads.py", TP, "query", "--account", E)
def threat(ts, comp, field):
    c = [x for x in ts if x["competitor_id"] == comp and x["thread_type"] in ("displacement_risk", "competitive_pursuit") and x["status"] == "active"]
    return c[0][field].split(" (")[0] if c else "none"
prev = {"account_id": E, "as_of": PD, "domains": {
  "financial_state": {"account_revenue_ttm": v(ttm_prev, src("billing"), PD), "account_gross_margin_month": v(margin[-2], src("ERP"), PD), "account_dso_days": v(qd(quarters[-2]), src("ERP"), PD),
                      "cost_to_serve_ratio": v(qc(quarters[-2]), src("ERP"), PD), "customer_fcf_margin": v(0.185, "public: Sanofi FY2025 results", "2026-01-29")},
  "marketing_state": {"engagement_score": v(mu_prev["engagement_score"]["current"], src("MAP"), PD), "executive_touches": v(mu_prev["executive_engagement"]["current"], src("MAP"), PD),
                      "intent_signals": v(mu_prev["buying_intent"]["current"], src("intent provider"), PD), "hr_campaign_status": v("active", src("MAP"), PD)},
  "competitive_state": {f"{c}:{f}": v(threat(thr_prev, c, fld), src("thread engine"), PD) for c in ("Competitor X", "Competitor Z", "Competitor Q") for f, fld in (("risk", "risk_level"), ("momentum", "momentum"))},
  "relationship_state": {"C-D:strength": v("Strong", src("relationship review"), PD), "C-A:last_meeting": v("2026-06-18", src("meeting log"), PD), "C-F:strength": v("Medium", src("relationship review"), PD)},
  "commercial_state": {"OPP-01:probability": v(0.80, src("CRM"), PD), "OPP-02:probability": v(0.35, src("CRM"), PD), "OPP-04:probability": v(0.30, src("CRM"), PD),
                       "OPP-07:close_date": v("2027-03-31", src("CRM"), PD), "pipeline_total_m": v(62.4, src("CRM"), PD)},
  "market_state": {"customer_2026_guidance": v("high single-digit sales growth", "public: Sanofi FY2025 results", "2026-01-29")},
  "operational_state": {"sla_attainment": v(0.989, src("service desk"), PD), "open_escalations": v(1, src("service desk"), PD), "csat": v(4.5, src("survey"), PD)}}}
cur = json.loads(json.dumps(prev)); cur["as_of"] = CD_; dm = cur["domains"]
dm["financial_state"].update(account_revenue_ttm=v(ttm_now, src("billing"), CD_), account_gross_margin_month=v(margin[-1], src("ERP"), CD_), account_dso_days=v(qd(quarters[-1]), src("ERP"), CD_),
    cost_to_serve_ratio=v(qc(quarters[-1]), src("ERP restated"), CD_, corrected=True))
dm["marketing_state"].update(engagement_score=v(mu_now["engagement_score"]["current"], src("MAP"), CD_), executive_touches=v(mu_now["executive_engagement"]["current"], src("MAP"), CD_),
                             intent_signals=v(mu_now["buying_intent"]["current"], src("intent provider"), CD_))
dm["marketing_state"].pop("hr_campaign_status")
dm["marketing_state"]["ai_campaign_influence"] = v("OPP-02 influenced (correlation)", src("MAP"), CD_)
dm["competitive_state"].update(**{f"{c}:{f}": v(threat(threads, c, fld), src("thread engine"), CD_) for c in ("Competitor X", "Competitor Z", "Competitor Q") for f, fld in (("risk", "risk_level"), ("momentum", "momentum"))})
dm["competitive_state"]["Competitor R:status"] = v("exiting HR services line", src("market news summary"), CD_)
dm["relationship_state"].update(**{"C-D:strength": v("Medium", src("relationship review"), CD_), "C-A:last_meeting": v("2026-09-24", src("meeting log"), CD_),
    "C-F:strength": v("Strong", src("relationship review"), CD_), "C-C:stance": {"value": "undecided", "sources": [{"value": "favours Competitor X", "source": src("AE notes")}, {"value": "neutral", "source": src("partner feedback")}]}})
dm["commercial_state"].update(**{"OPP-01:probability": v(0.70, src("CRM"), CD_), "OPP-02:probability": v(0.45, src("CRM"), CD_), "OPP-04:probability": v(0.35, src("CRM"), CD_),
    "OPP-07:close_date": v("2027-05-31", src("CRM"), CD_), "pipeline_total_m": v(round(sum(o["value_m"] for o in opps), 2), src("CRM"), CD_), "OPP-09:created": v("2026-09-28", src("CRM"), CD_)})
dm["operational_state"].update(sla_attainment=v(0.978, src("service desk"), CD_), open_escalations=v(3, src("service desk"), CD_), csat=v(4.3, src("survey"), CD_))
delta = run("domain_delta.py", W("prev.json", prev), W("cur.json", cur))
ops = [{"id": "sla_attainment", "label": "SLA attainment", "value": 0.978, "previous": 0.989, "unit": "ratio", "source": src("service desk")},
       {"id": "open_escalations", "label": "Open escalations", "value": 3, "previous": 1, "unit": "count", "source": src("service desk"), "higher_is_worse": True},
       {"id": "csat", "label": "Customer satisfaction (1–5)", "value": 4.3, "previous": 4.5, "unit": "score", "source": src("survey")},
       {"id": "utilization", "label": "Delivery team utilization", "value": 0.86, "previous": 0.83, "unit": "ratio", "source": src("resource plan")},
       {"id": "backlog", "label": "Service backlog (tickets)", "value": 142, "previous": 118, "unit": "count", "source": src("service desk"), "higher_is_worse": True}]
business_units = [{"name": "Business Unit A", "revenue_ttm_m": round(sum(rev[-12:]) * 0.46, 2), "revenue_prev_ttm_m": round(sum(rev[:12]) * 0.46 / 1.15 * (sum(rev[:12]) / sum(rev[:12])), 2), "gross_margin": round(margin[-1] + 0.01, 4)},
                  {"name": "Business Unit B", "revenue_ttm_m": round(sum(rev[-12:]) * 0.33, 2), "revenue_prev_ttm_m": round(sum(rev[-12:]) * 0.33 / 1.11, 2), "gross_margin": round(margin[-1] - 0.004, 4)},
                  {"name": "Business Unit C", "revenue_ttm_m": round(sum(rev[-12:]) * 0.21, 2), "revenue_prev_ttm_m": round(sum(rev[-12:]) * 0.21 / 1.06, 2), "gross_margin": round(margin[-1] - 0.02, 4)}]
business_units[0]["revenue_prev_ttm_m"] = round(business_units[0]["revenue_ttm_m"] / 1.15, 2)
for bu in business_units: bu["source"] = src("billing allocation by business unit")
peers = [{"account": "Account B", "revenue_m": 62.0, "prev_revenue_m": 57.4, "pipeline_m": 14.0, "risk": "Low", "series": [4.6, 4.8, 4.9, 5.0, 5.1, 5.2], "region": "North America", "source": src("billing")},
         {"account": "Account C", "revenue_m": 48.0, "prev_revenue_m": 49.5, "pipeline_m": 9.0, "risk": "High", "series": [4.3, 4.2, 4.1, 4.0, 3.9, 4.0], "region": "Europe", "source": src("billing")}]
decisions = [{"id": "DEC-01", "question": "Defend the renewal first, or lead with the AI transformation?", "options": [
    {"name": "Defend the renewal first", "financial_impact": "Protects $25.0M renewal (demo)", "risks": "Slower expansion"},
    {"name": "Lead with AI transformation", "financial_impact": "Adds $8.0M pipeline (demo)", "risks": "Competitor X thread is accelerating"}],
    "recommendation": "Defend the renewal, then expand", "confidence": 0.62, "owner": "Account Director", "deadline": "2026-10-31", "status": "awaiting decision", "source": src("decision record")}]
bundle = {"bundle_version": "1.0", "provider": "demo_provider.py", "data_mode": "demo", "data_notice": DEMO + ". Only the published financial figures and events of the demo entity are real, and each shows its source.",
          "entity": {"id": E.lower(), "name": E, "segment": "Global Enterprise", "period": "FY2026", "tenant": os.environ.get("GROWTH_TENANT", "demo-tenant")},
          "as_of": ASOF, "series": series, "annotations": annotations, "opportunities": opps, "executives": execs, "marketing": mk, "campaigns": camps,
          "financial_public": fi, "account_economics": quarters, "threads": threads, "relationship_signals": rel, "correlation": cd, "delta": delta,
          "delta_snapshots": {"previous": prev, "current": cur}, "operations": ops, "peers": peers, "business_units": business_units, "scenario_specs": scenario_specs, "decisions": decisions, "market_events": json.load(open(os.path.join(REF, "sanofi_events_PUBLIC.json"))) if E == "Sanofi" else [],
          "initiatives": inits, "engines_run": ["marketing_signals.py", "financial_intel.py", "competitive_threads.py", "cross_domain_correlator.py", "domain_delta.py"],
          "memory_db": MEM if a.memory_db else None}
json.dump(bundle, open(a.out, "w"), indent=1, default=str)
print(json.dumps({"bundle": a.out, "opportunities": len(opps), "executives": len(execs), "marketing_signals_account": sum(1 for s in msig if s["account_id"] == E),
                  "threads": len(threads), "competitors": len({t["competitor_id"] for t in threads}), "delta_items": sum(sum(len(x) for x in d.values()) for d in delta["domains"].values()),
                  "public_financial_signals": len(fi["signals"]) if fi else 0}))
