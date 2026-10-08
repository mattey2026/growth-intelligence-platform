#!/usr/bin/env python3
"""
run_v71.py: V7.1 test suite (no model calls, no network). Run from the plugin root: python3 tests/run_v71.py
Covers: Marketing (MKT), Financial (FIN), Competitive Threads (THR), Growth Signal Correlation (COR), Orchestration (ORC),
Digital Twin (TWN), Memory (MEM), Evidence/Governance (EVG), Observability (OBS), Cross-functional incl. Sanofi E2E (D21),
business-model adaptability (D22) and missing-data degradation (D23).
"""
import subprocess, json, os, sys, shutil, tempfile, sqlite3, glob, yaml
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")); import build_fixtures; build_fixtures.ensure()   # rebuild binary fixtures from readable SQL/JSON sources
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..")); FX = f"{ROOT}/tests/fixtures"; SK = f"{ROOT}/skills"
S = lambda skill, f: f"{SK}/{skill}/scripts/{f}"
OS = lambda f: S("business-orchestrator", f)
TMP = tempfile.mkdtemp(); MEM = f"{TMP}/mem.db"; shutil.copy(f"{FX}/growth_memory_v7.db", MEM)
R = []
def run(*a, env=None):
    p = subprocess.run([sys.executable, *a], capture_output=True, text=True, cwd=ROOT, env={**os.environ, **(env or {})})
    try: return p.returncode, json.loads(p.stdout)
    except Exception: return p.returncode, (p.stdout + p.stderr)
def T(area, name, cond, detail=""):
    R.append((area, name, bool(cond), detail))
def F(n): return f"{FX}/{n}"
# ================= MARKETING (10+) =================
c, mk = run(OS("marketing_signals.py"), "--signals", F("sanofi_marketing_SYNTHETIC.json"), "--contacts", F("sanofi_contacts_SYNTHETIC.json"), "--opportunities", F("sanofi_opps_SYNTHETIC.json"),
            "--campaigns", F("sanofi_campaigns_SYNTHETIC.json"), "--initiatives", F("sanofi_initiatives.json"), "--model", "B2B", "--asof", "2026-09-30", "--memory-db", MEM, "--out", f"{TMP}/mk.json")
u = mk["units"]["Sanofi"]; nz = mk["normalization"]
T("MKT", "1 ingest all signals", nz["received"] == 14, f"received {nz['received']}")
T("MKT", "2 normalize: dedupe, reject bad dates, flag unknown types", nz["duplicates_removed"] == 1 and len(nz["rejected"]) == 1 and nz["unclassified"] == ["podcast_listen"], json.dumps({k: nz[k] if not isinstance(nz[k], list) else len(nz[k]) for k in nz}))
T("MKT", "3 account engagement change identified", u["engagement_score"]["direction"] == "up" and u["engagement_score"]["material"], f"{u['engagement_score']['previous']} → {u['engagement_score']['current']} ({u['engagement_score']['change_pct']}%)")
T("MKT", "4 executive engagement identified by role", u["executive_engagement"]["current"] >= 3 and "CIO" in u["executive_engagement"]["roles"], f"roles {u['executive_engagement']['roles']}")
T("MKT", "5 buying-intent surge identified", u["buying_intent"]["surge"] and "demo_request" in u["buying_intent"]["types"], f"intent {u['buying_intent']['current']} vs {u['buying_intent']['previous']}")
T("MKT", "6 campaigns connected to accounts", mk["campaigns"]["CMP-AI"]["accounts"] == ["Sanofi"], "CMP-AI → Sanofi")
inf = {i["opportunity_id"]: i for i in mk["campaigns"]["CMP-AI"]["opportunities_influenced"]}   # per campaign (OPP-SAN-1 is touched by two campaigns)
T("MKT", "7 campaigns connected to opportunities (touch before creation)", "OPP-SAN-1" in inf and inf["OPP-SAN-1"]["touches_before_creation"] >= 3, f"OPP-SAN-1 touches {inf.get('OPP-SAN-1', {}).get('touches_before_creation')}")
fin_inf = [i for i in mk["campaigns"]["CMP-FIN"]["opportunities_influenced"] if i["opportunity_id"] == "OPP-SAN-2"]
T("MKT", "8 correlation vs causation distinguished", inf["OPP-SAN-1"]["claim_type"] == "CORRELATION" and fin_inf and fin_inf[0]["claim_type"] == "CAUSAL_ESTIMATE", "CMP-AI correlation; CMP-FIN has holdout → causal estimate")
h = [x for x in mk["hypotheses"] if x["type"] == "expansion"]
T("MKT", "9 evidence-backed commercial hypothesis", h and h[0]["claim_type"] == "HYPOTHESIS" and h[0]["evidence"] and "INI-1" in h[0]["initiatives"], f"conf {h[0]['confidence'] if h else None}")
_, q1 = run(OS("memory_graph.py"), MEM, "obj-query", "--type", "MarketingSignal", "--account", "Sanofi"); _, q2 = run(OS("memory_graph.py"), MEM, "obj-query", "--type", "CampaignInfluence", "--opportunity", "OPP-SAN-1")
T("MKT", "10 signals persisted to Business Memory", len(q1) == nz["normalized"] == 12 and len(q2) >= 1, f"{len(q1)} MarketingSignal, {len(q2)} CampaignInfluence for OPP-SAN-1")
_, mkb = run(OS("marketing_signals.py"), "--signals", F("b2c_marketing_SYNTHETIC.json"), "--model", "B2C", "--asof", "2026-09-30")
T("MKT", "11 B2C adaptation: segments, no executive engagement", mkb["unit"] == "segment" and mkb["units"]["young-urban"]["executive_engagement"] is None and any(x["type"] == "segment_demand" for x in mkb["hypotheses"]), "unit = segment")
# ================= FINANCIAL (10+) =================
_, fi = run(OS("financial_intel.py"), "--facts", F("sanofi_financials_PUBLIC.json"), "--events", F("sanofi_events_PUBLIC.json"), "--public", "--memory-db", MEM, "--out", f"{TMP}/fi.json")
m = fi["metrics"]["FY2025"]
T("FIN", "1 revenue growth deterministic (reported +6.2%)", abs(m["revenue_growth"]["value"] - 0.0620) < 0.0006, f"{m['revenue_growth']['value']:.4f}")
T("FIN", "2 gross margin matches reported 77.5%", abs(m["gross_margin"]["value"] - 0.775) < 0.001, f"{m['gross_margin']['value']:.4f}")
T("FIN", "3 operating margin matches reported 27.8%", abs(m["operating_margin"]["value"] - 0.278) < 0.001, f"{m['operating_margin']['value']:.4f}")
T("FIN", "4 FCF margin matches reported 18.5%", abs(m["fcf_margin"]["value"] - 0.185) < 0.001, f"{m['fcf_margin']['value']:.4f}")
miss = [x["metric"] for x in fi["missing"]["FY2025"]]
T("FIN", "5 EBITDA never fabricated (absent, reported missing)", "ebitda" not in m and "ebitda" in miss and "net_debt_to_ebitda" in miss, "EBITDA, EBITDA margin, leverage missing")
T("FIN", "6 capex / DSO / cash / working capital missing, not estimated", all(k in miss for k in ["capex", "dso", "cash", "working_capital"]) and not any(k in m for k in ["capex", "dso", "cash"]), str(miss))
T("FIN", "7 provenance: every derived metric lists sourced inputs", all(i["source"] and i["source_date"] for x in m.values() for i in x["inputs"]), "source + date on every input")
T("FIN", "8 secondary source down-weighted and disclosed", m["net_debt"]["confidence"] == 0.7 and fi["data_quality"]["secondary_sources"], "net debt conf 0.7")
kinds = {s["kind"]: s for s in fi["signals"]}
T("FIN", "9 signals + facts vs hypotheses", {"margin_expansion", "operating_leverage", "cash_generation_improving", "m_and_a"} <= set(kinds) and kinds["m_and_a"]["claim_type"] == "FACT" and all(i["claim_type"] == "HYPOTHESIS" for i in fi["commercial_implications"]), sorted(kinds))
_, fb = run(OS("financial_intel.py"), "--facts", F("b2c_financials_SYNTHETIC.json"), "--model", "B2C", "--out", f"{TMP}/fb.json")
fbm = fb["metrics"]["FY2025"]
T("FIN", "10 trends and material changes (decline case)", {"revenue_decline", "margin_pressure", "investment_reduction"} <= {s["kind"] for s in fb["signals"]} and fb["material_changes"], [s["kind"] for s in fb["signals"]])
T("FIN", "11 DSO and FCF computed deterministically", abs(fbm["dso"]["value"] - 45 / 1116 * 365) < 1e-3 and fbm["free_cash_flow"]["value"] == 39 and fbm["free_cash_flow"]["formula"] == "operating_cash_flow − capex", f"DSO {fbm['dso']['value']:.2f}; FCF {fbm['free_cash_flow']['value']}")
json.dump([{"entity": "X", "period": "FY2025", "metric": "revenue", "value": 100, "source": "s", "basis": "reported"}, {"entity": "X", "period": "FY2025", "metric": "ebitda", "value": 30, "source": "guess", "basis": "estimate"}], open(f"{TMP}/est.json", "w"))
_, fe = run(OS("financial_intel.py"), "--facts", f"{TMP}/est.json")
T("FIN", "12 estimates never promoted to facts", "ebitda" not in fe["metrics"]["FY2025"] and "ebitda" in fe["data_quality"]["estimates_excluded"], "estimate excluded")
_, fq = run(OS("memory_graph.py"), MEM, "obj-query", "--type", "FinancialMetric", "--account", "Sanofi", "--since", "FY2025", "--until", "FY2025")
T("FIN", "13 financial metrics persisted, queryable by time", len(fq) >= 10 and all(o["observed_at"] == "FY2025" for o in fq), f"{len(fq)} FY2025 metrics")
# ================= COMPETITIVE THREADS (16+) =================
CT = OS("competitive_threads.py")
_, ing = run(CT, MEM, "ingest", F("sanofi_competitor_signals_SYNTHETIC.json"))
x = [r for r in ing if r.get("thread_id") and r["signal"].startswith("CX")]
tid = x[0]["thread_id"]
T("THR", "1 create thread from first signal", x[0]["action"] == "CREATED", tid)
T("THR", "2 three signals → ONE thread (not three observations)", len({r["thread_id"] for r in x}) == 1 and [r["action"] for r in x] == ["CREATED", "UPDATED", "UPDATED"], [r["action"] for r in x])
_, t = run(CT, MEM, "get", tid)
T("THR", "3 chronology maintained in order", [c_["kind"] for c_ in t["chronology"]] == ["rfp_participation", "pricing_undercut", "champion_weakening"], "rfp → pricing → champion")
T("THR", "4 signal velocity calculated", t["signal_velocity"] > 0, f"{t['signal_velocity']} signals / 30 days")
T("THR", "5 acceleration identified", t["momentum"] == "accelerating", t["momentum"])
T("THR", "6 risk level and confidence updated", t["risk_level"] == "High" and x[-1]["confidence_after"] > x[0]["confidence_after"], f"risk {t['risk_level']}; conf {x[0]['confidence_after']} → {x[-1]['confidence_after']}")
y = [r for r in ing if r["signal"] == "CY1"][0]
_, ty = run(CT, MEM, "get", y["thread_id"])
T("THR", "7 separate competitor → separate thread (displacement opportunity)", y["thread_id"] != tid and ty["thread_type"] == "displacement_opportunity" and ty["opportunity_level"] in ("Medium", "High"), ty["thread_type"])
T("THR", "7b opportunity thread: competitor weakness counts as SUPPORT (not counter-evidence)", ty["confidence"] >= 0.4 and not ty["counter_evidence"] and "losing ground" in ty["hypotheses"][0]["text"] and not ty["momentum"].startswith("weakening"),
  f"conf {ty['confidence']}, momentum {ty['momentum']}")
T("THR", "8 links: opportunity, stakeholder, relationship signal", "OPP-SAN-2" in t["opportunities"] and "C-SAN-2" in t["stakeholders"] and "R-1" in t["relationship_signals"], "")
_, lk = run(CT, MEM, "link", tid, "--campaign", "CMP-FIN", "--financial-signal", kinds["m_and_a"]["signal_id"], "--market-signal", "INI-2")
T("THR", "9 links: campaigns, financial signals, market signals", "CMP-FIN" in lk["campaigns"] and lk["financial_signals"] and "INI-2" in lk["market_signals"], "")
T("THR", "10 predicted next event (labelled PREDICTION)", t["predicted_next_event"]["claim_type"] == "PREDICTION" and t["predicted_next_event"]["event"], t["predicted_next_event"]["event"])
T("THR", "11 recommended actions need approval", any("champion" in a_["action"].lower() for a_ in t["recommended_actions"]) and all(a_["approval_required"] for a_ in t["recommended_actions"]), [a_["action"] for a_ in t["recommended_actions"]])
json.dump([{"signal_id": "CX4", "account_id": "Sanofi", "competitor_id": "Competitor X", "observed_at": "2026-09-28", "kind": "our_win_against", "source": "win notice (synthetic)", "text": "We won the analytics pilot against Competitor X"},
           {"signal_id": "CX5", "account_id": "Sanofi", "competitor_id": "Competitor X", "observed_at": "2026-09-29", "kind": "customer_positive_on_us", "source": "exec sponsor note (synthetic)", "text": "CIO praised our delivery"}], open(f"{TMP}/cx45.json", "w"))
_, ing2 = run(CT, MEM, "ingest", f"{TMP}/cx45.json")
_, t2 = run(CT, MEM, "get", tid)
T("THR", "12 contradictory evidence captured on the same thread", all(r["thread_id"] == tid for r in ing2) and len(t2["counter_evidence"]) == 2, f"{len(t2['counter_evidence'])} counter-evidence items")
T("THR", "13 weakening identified", t2["momentum"].startswith("weakening") and t2["confidence"] < t["confidence"], f"{t2['momentum']}; conf {t['confidence']} → {t2['confidence']}")
_, oc = run(CT, MEM, "outcome", tid, "--outcome", "won", "--date", "2026-10-15", "--evidence", "award letter (synthetic)")
_, t3 = run(CT, MEM, "get", tid)
T("THR", "14 resolution and outcome recorded", t3["status"] == "resolved" and t3["outcome"] == "won" and oc["prediction_was"], "prediction at close kept for learning")
_, qa = run(CT, MEM, "query", "--competitor", "Competitor X"); _, qo = run(CT, MEM, "query", "--opportunity", "OPP-SAN-2")
T("THR", "15 persistent + retrievable in a new process (by competitor / opportunity)", qa and qa[0]["thread_id"] == tid and qo and qo[0]["thread_id"] == tid, "fresh process reads the thread")
json.dump([{"signal_id": "BAD1", "account_id": "Sanofi", "competitor_id": "Competitor X", "observed_at": "2026-09-30", "kind": "rumour", "source": "x"},
           {"signal_id": "BAD2", "account_id": "Sanofi", "competitor_id": "Competitor X", "observed_at": "2026-09-30", "kind": "rfp_participation"},
           {"signal_id": "CX1", "account_id": "Sanofi", "competitor_id": "Competitor X", "observed_at": "2026-07-15", "kind": "rfp_participation", "source": "dup"}], open(f"{TMP}/bad.json", "w"))
_, bd = run(CT, MEM, "ingest", f"{TMP}/bad.json")
T("THR", "16 unknown kinds / missing sources rejected; duplicates ignored", sorted(r["action"] for r in bd) == ["DUPLICATE_IGNORED", "REJECTED", "REJECTED"], [r["action"] for r in bd])
TM = f"{TMP}/ten.db"; shutil.copy(MEM, TM); run(OS("memory_graph.py"), TM, "stats", env={"GROWTH_TENANT": "tenant-a"})
cten, _ = run(CT, TM, "query", env={"GROWTH_TENANT": "tenant-b"})
T("THR", "17 threads are tenant-isolated", cten == 3, "tenant-b refused on tenant-a memory")
_, cto = run(OS("memory_graph.py"), MEM, "obj-query", "--type", "CompetitiveOutcome", "--competitor", "Competitor X")
T("THR", "18 CompetitiveOutcome persisted for learning", len(cto) == 1 and cto[0]["data"]["outcome"] == "won", "")
# ================= GROWTH SIGNAL CORRELATION (10+) =================
_, thq = run(CT, MEM, "query", "--account", "Sanofi"); json.dump(thq, open(f"{TMP}/th_all.json", "w"))
MEM2 = f"{TMP}/mem2.db"; shutil.copy(f"{FX}/growth_memory_v7.db", MEM2); run(CT, MEM2, "ingest", F("sanofi_competitor_signals_SYNTHETIC.json"))
_, thq2 = run(CT, MEM2, "query", "--account", "Sanofi"); json.dump(thq2, open(f"{TMP}/th.json", "w"))
CD = OS("cross_domain_correlator.py")
_, cd = run(CD, "--account", "Sanofi", "--marketing", f"{TMP}/mk.json", "--financial", f"{TMP}/fi.json", "--threads", f"{TMP}/th.json", "--relationship", F("sanofi_relationship_SYNTHETIC.json"),
            "--initiatives", F("sanofi_initiatives.json"), "--memory-db", MEM2, "--out", f"{TMP}/cd.json")
P = {p["pattern_id"]: p for p in cd["patterns"]}
T("COR", "1 P1 marketing→growth detected with evidence", P["P1"]["status"] == "detected" and P["P1"]["supporting_evidence"], P["P1"]["components_present"])
T("COR", "2 P4 competitive displacement detected (RFP + champion weakening)", P["P4"]["status"] == "detected" and P["P4"]["route_to"][0] == "competitive-thread-agent", P["P4"]["components_present"])
T("COR", "3 P5 compound ≥3 independent domains", P["P5"]["status"] == "detected" and len(P["P5"]["components_present"]) >= 3, P["P5"]["components_present"])
T("COR", "4 P2 not forced when evidence is absent (Sanofi margins expanding)", P["P2"]["status"] != "detected" and "margin pressure" in P["P2"]["missing_evidence"], P["P2"]["status"])
_, fit = run(OS("financial_intel.py"), "--facts", F("transformation_financials_SYNTHETIC.json"), "--events", F("transformation_events_SYNTHETIC.json"), "--out", f"{TMP}/fit.json")
_, cd2 = run(CD, "--account", "IndusCo", "--financial", f"{TMP}/fit.json")
P2 = {p["pattern_id"]: p for p in cd2["patterns"]}
T("COR", "5 P2 financial→growth (transformation) detected", P2["P2"]["status"] == "detected", P2["P2"]["components_present"])
_, cd3 = run(CD, "--account", "RetailCo", "--financial", f"{TMP}/fb.json"); P3 = {p["pattern_id"]: p for p in cd3["patterns"]}
T("COR", "6 P3 financial→risk detected", P3["P3"]["status"] == "detected" and P3["P3"]["route_to"][0] == "customer-growth-agent", P3["P3"]["components_present"])
T("COR", "7 patterns are HYPOTHESIS, never FACT, with cautions", all(p["claim_type"] in ("HYPOTHESIS", None) for p in cd["patterns"] + cd2["patterns"] + cd3["patterns"]) and all(p["caution"] for p in cd["patterns"] if p["status"] != "not_detected"), "")
_, fie = run(OS("financial_intel.py"), "--facts", F("transformation_financials_SYNTHETIC.json"), "--out", f"{TMP}/fie.json")   # no technology-investment event
_, cde = run(CD, "--account", "IndusCo", "--financial", f"{TMP}/fie.json")
em = [p for p in cde["patterns"] + cd["patterns"] if p["status"] == "emerging"]
T("COR", "8 emerging patterns: capped confidence + missing evidence", all(p["missing_evidence"] and p["confidence"] <= 0.5 for p in em) and em, [(p["pattern_id"], p["confidence"]) for p in em])
_, cdo = run(OS("memory_graph.py"), MEM2, "obj-query", "--type", "CrossDomainPattern", "--account", "Sanofi")
T("COR", "9 patterns written to memory", len(cdo) == len([p for p in cd["patterns"] if p["status"] != "not_detected"]), f"{len(cdo)} CrossDomainPattern objects")
reg = {yaml.safe_load(open(f_))["agent_id"] for f_ in glob.glob(f"{ROOT}/registry/manifests/*.yaml") if not os.path.basename(f_).startswith("_")} | {"business-orchestrator"}
T("COR", "10 every route resolves to a registered agent", all(r_ in reg for p in cd["patterns"] + cd2["patterns"] + cd3["patterns"] if p["route_to"] for r_ in p["route_to"]), "")
_, cdn = run(CD, "--account", "Sanofi", "--financial", f"{TMP}/fi.json", "--threads", f"{TMP}/th.json")
T("COR", "11 missing domain lowers certainty (no marketing data)", {p["pattern_id"]: p for p in cdn["patterns"]}["P1"]["status"] == "not_detected" and "marketing" in cdn["data_gaps"], cdn["data_gaps"])
# ================= ORCHESTRATION (5+) =================
NEW = {"marketing-intelligence-agent", "financial-intelligence-agent", "competitive-thread-agent"}
exp = {"What's changing in this account?": NEW, "Show me the financial story.": {"financial-intelligence-agent"}, "What is marketing telling us?": {"marketing-intelligence-agent"},
       "Where are competitors gaining ground?": {"competitive-thread-agent"}, "Find the biggest growth opportunities.": NEW, "Build a complete account strategy.": NEW}
for i, (qq, need) in enumerate(exp.items(), 1):
    _, pl = run(OS("agent_planner.py"), qq, "--memory-db", MEM)
    T("ORC", f"{i} '{qq}' discovers {sorted(need)}", need <= set(pl["agents"]), pl["intent"])
def topo_ok(pl_):
    seen_, names_ = set(), {s_["step"] for s_ in pl_["steps"]}
    for s_ in pl_["steps"]:
        if any(d_ in names_ and d_ not in seen_ for d_ in s_["depends_on"]): return False
        seen_.add(s_["step"])
    return True
plans_ = [run(OS("agent_planner.py"), qq, "--memory-db", MEM)[1] for qq in list(exp) + ["Build a complete growth strategy for Sanofi and identify the highest-value opportunities, major risks, financial drivers, marketing signals, and competitive threats."]]
T("ORC", "8 every plan lists steps after their dependencies", all(topo_ok(p_) for p_ in plans_), f"{len(plans_)} plans checked")
MD = f"{TMP}/manifests"; shutil.copytree(f"{ROOT}/registry/manifests", MD)
mm = yaml.safe_load(open(f"{MD}/marketing-intelligence-agent.yaml")); mm["status"] = "DISABLED"; yaml.safe_dump(mm, open(f"{MD}/marketing-intelligence-agent.yaml", "w"))
cust = yaml.safe_load(open(f"{MD}/_template.yaml")); cust.update(agent_id="sanofi-account-agent", status="EXPERIMENTAL", serves_intents=["account_strategy"]); yaml.safe_dump(cust, open(f"{MD}/sanofi-account-agent.yaml", "w"))
_, pld = run(OS("agent_planner.py"), "Build a complete account strategy.", "--manifests", MD)
T("ORC", "7 disabled agent excluded; customer agent discovered via manifest only", "marketing-intelligence-agent" not in pld["agents"] and "sanofi-account-agent" in pld["agents"], "no planner change needed")
# ================= DIGITAL TWIN (5+) =================
TW = OS("twin_state.py")
_, s1 = run(TW, MEM2, "snapshot", "Sanofi", "--as-of", "2026-09-30")
T("TWN", "1 snapshot has explicit state domains", {"financial_state", "marketing_state", "competitive_state", "competitive_threads", "relationship_state", "commercial_state", "market_state", "operational_state"} == set(s1["domain_sizes"]), s1["domain_sizes"])
run(OS("financial_intel.py"), "--facts", F("sanofi_financials_PUBLIC.json"), "--events", F("sanofi_events_PUBLIC.json"), "--public", "--memory-db", MEM2)
run(OS("marketing_signals.py"), "--signals", F("sanofi_marketing_SYNTHETIC.json"), "--contacts", F("sanofi_contacts_SYNTHETIC.json"), "--asof", "2026-09-30", "--memory-db", MEM2)
_, s2 = run(TW, MEM2, "snapshot", "Sanofi", "--as-of", "2026-10-01")
T("TWN", "2 twin updates when financial and marketing data change", s2["domain_sizes"]["financial_state"] > s1["domain_sizes"]["financial_state"] and s2["domain_sizes"]["marketing_state"] > 0, f"financial {s1['domain_sizes']['financial_state']} → {s2['domain_sizes']['financial_state']}")
run(CT, MEM2, "ingest", f"{TMP}/cx45.json"); _, s3 = run(TW, MEM2, "snapshot", "Sanofi", "--as-of", "2026-10-02")
_, ch = run(TW, MEM2, "changes", "Sanofi")
T("TWN", "3 'what changed since the previous snapshot' after competitor signals", "competitive_threads" in ch["domains"] and ch["domains"]["competitive_threads"]["changed"], ch.get("summary"))
T("TWN", "4 unchanged domains not recomputed", "financial_state" in ch["unchanged_domains"] and "financial_state" not in ch["recompute"], ch["unchanged_domains"])
ctg, _ = run(TW, MEM2, "set", "Sanofi", "--state", "target", "--domain", "commercial_state", "--metrics", '{"bookings": 5000000}', "--horizon", "2027-09-30", "--source", "plan")
run(TW, MEM2, "set", "Sanofi", "--state", "forecast", "--domain", "financial_state", "--metrics", '{"revenue_growth_2026": "high single digit"}', "--horizon", "2026-12-31", "--source", "Sanofi 2026 guidance")
run(TW, MEM2, "set", "Sanofi", "--state", "target", "--domain", "commercial_state", "--metrics", '{"bookings": 5000000}', "--horizon", "2027-09-30", "--source", "plan", "--set-by", "account director")
_, vw = run(TW, MEM2, "view", "Sanofi")
T("TWN", "5 HISTORICAL / CURRENT / FORECAST / TARGET kept separate; TARGET needs an owner", ctg == 1 and len(vw["HISTORICAL"]) == 2 and vw["FORECAST"] and vw["TARGET"] and "FORECAST" not in json.dumps(vw["CURRENT"]), f"{len(vw['HISTORICAL'])} historical snapshots")
# ================= MEMORY (5+) =================
types = {r[0] for r in sqlite3.connect(MEM).execute("SELECT DISTINCT obj_type FROM domain_objects")}
need9 = {"MarketingSignal", "FinancialSignal", "FinancialMetric", "CompetitiveEvent", "CompetitiveThread", "CompetitiveHypothesis", "CompetitiveOutcome", "CampaignInfluence", "AccountEngagement"}
T("MEM", "1 all nine required object types persisted", need9 <= types, sorted(need9 - types) or "all present")
rows = [dict(zip([d[0] for d in cur.description], r)) for cur in [sqlite3.connect(MEM).execute("SELECT * FROM domain_objects")] for r in cur.fetchall()]
T("MEM", "2 timestamped, source-linked, tenant-scoped", all(r_["observed_at"] and r_["source"] and r_["tenant"] for r_ in rows), f"{len(rows)} objects")
T("MEM", "3 confidence-scored where applicable", sum(1 for r_ in rows if r_["confidence"] is not None) / len(rows) > 0.9, "")
_, a1 = run(OS("memory_graph.py"), MEM, "obj-query", "--account", "Sanofi"); _, a2 = run(OS("memory_graph.py"), MEM, "obj-query", "--competitor", "Competitor X")
_, a3 = run(OS("memory_graph.py"), MEM, "obj-query", "--opportunity", "OPP-SAN-2"); _, a4 = run(OS("memory_graph.py"), MEM, "obj-query", "--since", "2026-09-01", "--until", "2026-09-30")
T("MEM", "4 queryable by account / competitor / opportunity / time", all(len(x_) > 0 for x_ in (a1, a2, a3, a4)), [len(x_) for x_ in (a1, a2, a3, a4)])
json.dump([{"obj_type": "FinancialMetric", "account_id": "Sanofi", "observed_at": "FY2025"}, {"obj_type": "Gossip", "account_id": "Sanofi", "observed_at": "2026-01-01", "source": "x"}], open(f"{TMP}/badobj.json", "w"))
_, bo = run(OS("memory_graph.py"), MEM, "obj-put", f"{TMP}/badobj.json")
T("MEM", "5 objects without a source or with an unknown type rejected", bo["stored"] == 0 and len(bo["rejected"]) == 2, "")
TM2 = f"{TMP}/ten2.db"; shutil.copy(MEM, TM2); run(OS("memory_graph.py"), TM2, "stats", env={"GROWTH_TENANT": "acme"})
cq, _ = run(OS("memory_graph.py"), TM2, "obj-query", "--account", "Sanofi", env={"GROWTH_TENANT": "globex"})
T("MEM", "6 another tenant cannot read the objects", cq == 3, "refused")
# ================= EVIDENCE / GOVERNANCE (5+) =================
EVV = OS("evidence_validator.py")
src = {"financial_facts": [{"entity": "Sanofi", "metric": "revenue", "period": "FY2025", "value": 43626}], "campaigns": ["CMP-AI", "CMP-FIN"], "signals": ["MS06"],
       "competitors": ["Competitor X", "Competitor Y"], "evidence": {"PR-2026": {"date": "2026-01-29", "source": "Sanofi PR"}, "OLD": {"date": "2023-01-01", "source": "old"}}}
json.dump(src, open(f"{TMP}/src.json", "w"))
claims = [{"claim_type": "FACT", "text": "Sanofi FY2025 revenue €43,626m", "entity": "Sanofi", "metric": "revenue", "period": "FY2025", "value": 43626, "evidence": ["PR-2026"]},
          {"claim_type": "FACT", "text": "Sanofi FY2025 EBITDA €15.1bn", "entity": "Sanofi", "metric": "ebitda", "period": "FY2025", "value": 15100, "evidence": ["PR-2026"]},
          {"claim_type": "CORRELATION", "text": "CMP-GHOST drove the deal", "campaign_ids": ["CMP-GHOST"], "evidence": ["MS06"]},
          {"claim_type": "FACT", "text": "Competitor Z is in the RFP", "competitor": "Competitor Z", "evidence": ["PR-2026"]},
          {"claim_type": "CORRELATION", "text": "The AI webinar caused the opportunity", "campaign_ids": ["CMP-AI"], "evidence": ["MS06"]},
          {"claim_type": "FACT", "text": "Old headcount figure", "evidence": ["OLD"]},
          {"claim_type": "FACT", "text": "Unsupported statement", "evidence": []},
          {"claim_type": "HYPOTHESIS", "text": "Sanofi may expand AI automation", "evidence": ["MS06"]}]
json.dump(claims, open(f"{TMP}/claims.json", "w"))
_, ev = run(EVV, "claims", f"{TMP}/claims.json", "--sources", f"{TMP}/src.json", "--asof", "2026-09-30")
res = [c_["result"] for c_ in ev["claims"]]
T("EVG", "1 sourced fact passes; fabricated financial value rejected", res[0] == "ok" and res[1] == "reject", ev["claims"][1]["issues"])
T("EVG", "2 fabricated marketing activity rejected", res[2] == "reject" and any("fabricated marketing" in i for i in ev["claims"][2]["issues"]), "")
T("EVG", "3 unsupported competitor claim rejected", res[3] == "reject", ev["claims"][3]["issues"])
T("EVG", "4 causal language on a correlation rejected", res[4] == "reject" and any("causal" in i for i in ev["claims"][4]["issues"]), "")
T("EVG", "5 stale evidence flagged; unsupported claim rejected; hypothesis allowed", res[5] == "flag" and res[6] == "reject" and res[7] == "ok", res[5:])
json.dump([dict(claims[0]), dict(claims[0], value=41000, text="conflict")], open(f"{TMP}/conf.json", "w"))
_, evc = run(EVV, "claims", f"{TMP}/conf.json", "--sources", f"{TMP}/src.json")
T("EVG", "6 conflicting financial values rejected", evc["summary"]["reject"] == 2, "")
POL = F("tenant-policy.example.yaml")
def gate(req):
    f = f"{TMP}/rq.json"; json.dump(req, open(f, "w")); return run(OS("policy_gate.py"), ROOT, "--tenant-policy", POL, "--request", f)[1]
B = {"tenant": "demo-tenant", "user": {"id": "u", "role": "cro", "region": "EMEA"}, "record": {"region": "EMEA"}, "evidence": {"confidence": 0.8, "items": 3}}
g1 = gate(dict(B, agent="marketing-intelligence-agent", data=["financial_data"])); g2 = gate(dict(B, agent="relationship-agent", data=["financial_data"]))
g3 = gate(dict(B, user={"id": "s", "role": "seller", "region": "EMEA"}, agent="financial-intelligence-agent", data=["public_filings"], sensitivity=["financial_confidential"]))
g4 = gate(dict(B, agent="financial-intelligence-agent", data=["marketing_data"])); g5 = gate(dict(B, user={"id": "f", "role": "cfo", "region": "EMEA"}, agent="financial-intelligence-agent", data=["financial_data"], sensitivity=["financial_confidential"]))
g6 = gate(dict(B, user={"id": "s", "role": "seller", "region": "EMEA"}, agent="financial-intelligence-agent", data=["financial_data"]))
T("EVG", "7 unauthorized agents cannot access restricted financial / marketing data", all(g["decision"] == "DENY" for g in (g1, g2, g4)), [g1["reasons"][-1][:60], g4["reasons"][-1][:60]])
T("EVG", "8 user without clearance denied; CFO with clearance allowed", g3["decision"] == "DENY" and g6["decision"] == "DENY" and g5["decision"] == "ALLOW", [g3["decision"], g6["decision"], g5["decision"]])
_, cf = run(S("platform-admin", "registry.py"), ROOT, "can", "competitive-thread-agent", "--data", "financial_data")
T("EVG", "9 least privilege in the registry", cf["allowed"] is False, "")
json.dump([{"agent": "financial-intelligence-agent", "facts": [{"entity": "Sanofi", "attribute": "revenue_growth", "value": "6.2%", "source": "PR"}]},
           {"agent": "account-intelligence-agent", "facts": [{"entity": "Sanofi", "attribute": "revenue_growth", "value": "9.9%", "source": "CER"}]}], open(f"{TMP}/cfa.json", "w"))
_, cfl = run(EVV, "conflicts", f"{TMP}/cfa.json")
T("EVG", "10 cross-agent evidence conflict detected (reported vs CER growth)", cfl["count"] == 1, "")
# ================= OBSERVABILITY =================
TRF = f"{TMP}/tr.jsonl"; tid_ = subprocess.run([sys.executable, OS("trace.py"), TRF, "start", "--request", "Build a complete growth strategy for Sanofi", "--user", "u", "--tenant", "demo-tenant"], capture_output=True, text=True).stdout.strip()
for k, n in [("intent", "account_strategy"), ("context", "profile"), ("memory", "recall"), ("delta", "domain_delta"), ("plan", "agent_planner"), ("financial_analysis", "financial_intel"),
             ("marketing_signal_analysis", "marketing_signals"), ("competitive_thread_match", "CX2→CT"), ("competitive_thread_update", "CT"), ("cross_domain_correlation", "P1,P4,P5"),
             ("agent_escalation", "opportunity T2→T3"), ("step", "opportunity-agent"), ("evidence", "validator"), ("evidence_conflict", "growth reported vs CER"),
             ("confidence_change", "thread 0.67→0.54"), ("decision", "memo"), ("approval", "CRO"), ("action", "crm.create_task"), ("outcome", "pending")]:
    subprocess.run([sys.executable, OS("trace.py"), TRF, "span", tid_, "--kind", k, "--name", n, "--tier", "T2" if k == "step" else "T0"], capture_output=True)
cc, tck = run(OS("trace.py"), TRF, "check", tid_)
T("OBS", "1 complete trace: request → … → outcome in order", tck["complete"] and tck["order_ok"] and tck["stages_present"][-1] == "outcome", tck["stages_present"])
T("OBS", "2 all V7.1 trace events present", {"marketing_signal_analysis", "financial_analysis", "competitive_thread_match", "competitive_thread_update", "cross_domain_correlation", "evidence_conflict", "confidence_change", "agent_escalation"} <= set(tck["v71_events"]), tck["v71_events"])
TRB = f"{TMP}/trb.jsonl"; tb = subprocess.run([sys.executable, OS("trace.py"), TRB, "start", "--request", "x"], capture_output=True, text=True).stdout.strip()
subprocess.run([sys.executable, OS("trace.py"), TRB, "span", tb, "--kind", "plan"], capture_output=True); cb, tbk = run(OS("trace.py"), TRB, "check", tb)
T("OBS", "3 incomplete trace detected", cb == 1 and "memory" in tbk["core_missing"], tbk["core_missing"])
# ================= CROSS-FUNCTIONAL: SANOFI E2E (D21) =================
_, pl = run(OS("agent_planner.py"), "Build a complete growth strategy for Sanofi and identify the highest-value opportunities, major risks, financial drivers, marketing signals, and competitive threats.", "--memory-db", MEM)
req = {"research-agent", "account-intelligence-agent", "financial-intelligence-agent", "marketing-intelligence-agent", "competitive-thread-agent", "market-intelligence-agent",
       "relationship-agent", "opportunity-agent", "executive-decision-agent"}
T("XF", "D21.1 plan orchestrates all required domains (no skill or agent named)", pl["intent"] == "account_strategy" and req <= set(pl["agents"]) and any(s_["step"] == "twin_snapshot" for s_ in pl["steps"]),
  f"{len(pl['agents'])} agents, {len(pl['steps'])} steps; missing {sorted(req - set(pl['agents']))}")
_, op = run(OS("opportunity_builder.py"), "--account", "Sanofi", "--bundle", F("sanofi_bundle_SYNTHETIC.json"), "--correlation", f"{TMP}/cd.json", "--threads", f"{TMP}/th.json",
            "--marketing", f"{TMP}/mk.json", "--financial", f"{TMP}/fi.json", "--out", f"{TMP}/op.json")
fields = ["opportunity", "why_now", "business_driver", "evidence", "estimated_value", "confidence", "competitive_context", "stakeholders", "recommended_action", "risks", "missing_evidence"]
T("XF", "D15 every opportunity has all 11 fields", op["opportunities"] and all(all(f_ in o for f_ in fields) for o in op["opportunities"]), f"{op['count']} opportunities")
T("XF", "D15 no unsupported value presented as fact", all((o["estimated_value"].get("status") == "unsized") or (o["estimated_value"].get("basis") and o["estimated_value"].get("claim_type") in ("INTERNAL_ESTIMATE", "FACT_BASED_RANGE")) for o in op["opportunities"]),
  f"{op['sized']} sized with basis, {op['unsized']} unsized")
run(TW, MEM2, "snapshot", "Sanofi")
_, prof = run(S("business-context-discovery", "context_discovery.py"), F("workbook_v2_2026-10-13.xlsx"), "--out", f"{TMP}/prof.json")
_, plan = run(OS("account_plan_builder.py"), "--account", "Sanofi", "--profile", f"{TMP}/prof.json", "--financial", f"{TMP}/fi.json", "--marketing", f"{TMP}/mk.json", "--threads", f"{TMP}/th.json",
              "--correlation", f"{TMP}/cd.json", "--opportunities", f"{TMP}/op.json", "--bundle", F("sanofi_bundle_SYNTHETIC.json"), "--out", f"{TMP}/plan.json", "--md", f"{TMP}/plan.md")
secs = list(plan["sections"])
T("XF", "D11/D21.2 account plan has all 12 sections", len(secs) == 12 and all(v == "ok" for v in plan["section_status"].values()), plan["section_status"])
T("XF", "D21.3 every material conclusion has evidence", plan["conclusions"] > 20 and plan["conclusions_without_evidence"] == 0, f"{plan['conclusions']} conclusions, {plan['conclusions_without_evidence']} without evidence")
pj = json.dumps(plan)
T("XF", "D21.4 no fabricated Sanofi data (EBITDA/capex/DSO reported missing; internal data labelled synthetic)", "Not available: ebitda" in pj and "SYNTHETIC" in pj and "ebitda FY2025:" not in pj.lower(), "")
fin_claims = [{"claim_type": c_["claim_type"] if c_["claim_type"] != "DERIVED" else "INFERENCE", "text": c_["text"], "evidence": c_["evidence"]} for c_ in plan["sections"]["2_financial_position"]]
json.dump(fin_claims, open(f"{TMP}/fc.json", "w")); json.dump({"financial_facts": [], "evidence": {}}, open(f"{TMP}/s0.json", "w"))
_, fcv = run(EVV, "claims", f"{TMP}/fc.json", "--sources", f"{TMP}/s0.json")
T("XF", "D21.5 financial conclusions all typed and sourced", fcv["summary"]["reject"] == 0, fcv["summary"])
memo = {"situation": "Sanofi growth strategy", "options": [{"name": "Lead with AI automation", "summary": "", "financial_impact": "AI Services range 2.8–4.0M (internal estimate)", "strategic_impact": "", "risks": "Competitor X thread", "dependencies": "sponsor"},
        {"name": "Defend finance ops first", "summary": "", "financial_impact": "protects 6.0M footprint (synthetic)", "strategic_impact": "", "risks": "slower growth", "dependencies": ""}],
        "evidence": ["P1", "P4", "OPP list"], "trade_offs": "growth vs defense", "recommendation": "Defend, then expand", "confidence": 0.55, "what_would_change": "Competitor X loses the RFP",
        "decision_owner": "Account Director", "decision_deadline": "2026-10-31", "required_approval": "Account Director"}
json.dump(memo, open(f"{TMP}/memo.json", "w")); cm, _ = run(S("decision-intelligence", "decision_record.py"), MEM, "validate", f"{TMP}/memo.json")
T("XF", "D21.6 decision intelligence frames the options", cm == 0, "memo valid")
# ================= D22 business-model adaptability =================
_, pb2b = run(S("business-context-discovery", "context_discovery.py"), F("workbook_v1_2026-09-29.xlsx"))
_, pb2c = run(S("business-context-discovery", "context_discovery.py"), F("orders.csv"), F("customers.csv"))
_, pbb = run(S("business-context-discovery", "context_discovery.py"), F("b2b2c_channel_SYNTHETIC.csv"), "--out", f"{TMP}/pbb.json")
_, kbb = run(S("executive-command-center", "kpi_engine.py"), F("b2b2c_channel_SYNTHETIC.csv"), "--profile", f"{TMP}/pbb.json")
_, mbb = run(OS("marketing_signals.py"), "--signals", F("b2b2c_marketing_SYNTHETIC.json"), "--model", "B2B2C", "--asof", "2026-09-30")
_, fbb = run(OS("financial_intel.py"), "--facts", F("b2c_financials_SYNTHETIC.json"), "--model", "B2B2C")
_, obc = run(OS("opportunity_builder.py"), "--account", "young-urban", "--bundle", F("sanofi_bundle_SYNTHETIC.json"), "--correlation", f"{TMP}/cd.json", "--model", "B2C")
T("XF", "D22.1 B2B: account KPIs, executive engagement, account opportunities", pb2b["business_model"]["value"] == "B2B" and pb2b["kpi_framework"]["model"] == "B2B" and mk["unit"] == "account_id" and u["executive_engagement"], "")
T("XF", "D22.2 B2C: consumer KPIs, segment marketing, consumer financial reading", pb2c["kpi_framework"]["model"] in ("B2C", "D2C") and "AOV" in pb2c["kpi_framework"]["primary"] and mkb["unit"] == "segment"
  and any("Consumer demand" in i["implication"] for i in fb["commercial_implications"]), f"{pb2c['business_model']['value']}")
T("XF", "D22.3 B2B2C: channel KPIs, partner marketing, channel financial reading", pbb["kpi_framework"]["model"] == "B2B2C" and any(k["name"] == "Sell-through rate" for k in kbb["kpis"]) and mbb["unit"] == "partner_id"
  and any(h_["type"] == "channel_demand" for h_ in mbb["hypotheses"]) and any("Channel" in i["implication"] or "channel" in i["implication"] or "Sell-through" in i["implication"] for i in fbb["commercial_implications"]), "")
# ================= D23 missing data =================
_, n1 = run(OS("account_plan_builder.py"), "--account", "Sanofi", "--marketing", f"{TMP}/mk.json", "--threads", f"{TMP}/th.json", "--bundle", F("sanofi_bundle_SYNTHETIC.json"))
T("XF", "D23.1 no financial data: continues; section flagged with the evidence needed", n1["section_status"]["2_financial_position"] == "insufficient_evidence" and n1["section_status"]["4_marketing_engagement"] == "ok", n1["sections"]["2_financial_position"])
T("XF", "D23.2 no marketing data: P1 not asserted; gap reported", {p["pattern_id"]: p for p in cdn["patterns"]}["P1"]["status"] == "not_detected" and "marketing" in cdn["data_gaps"], "")
_, n3 = run(CD, "--account", "Sanofi", "--marketing", f"{TMP}/mk.json", "--financial", f"{TMP}/fi.json")
T("XF", "D23.3 no competitor data: P4 not asserted; confidence not inflated", {p["pattern_id"]: p for p in n3["patterns"]}["P4"]["status"] == "not_detected" and "competitive" in n3["data_gaps"], n3["data_gaps"])
_, n4 = run(OS("opportunity_builder.py"), "--account", "Sanofi", "--correlation", f"{TMP}/cd.json", "--financial", f"{TMP}/fi.json")
T("XF", "D23.4 no CRM data: opportunities from signals only, unsized, stakeholders missing", n4["count"] > 0 and n4["sized"] == 0 and all(o["stakeholders"] == [] for o in n4["opportunities"]), f"{n4['count']} unsized hypotheses")
T("XF", "D23.5 conflicting data flagged, not averaged", cfl["count"] == 1 and evc["summary"]["reject"] == 2, "")
T("XF", "D23.6 stale data flagged", res[5] == "flag", "")
json.dump([{"entity": "Y", "period": "FY2025", "metric": "revenue", "value": 500, "source": "10-K", "basis": "reported"}], open(f"{TMP}/partial.json", "w"))
_, n7 = run(OS("financial_intel.py"), "--facts", f"{TMP}/partial.json")
T("XF", "D23.7 partial data: computes what it can, lists what it cannot", "revenue" in n7["metrics"]["FY2025"] and len(n7["missing"]["FY2025"]) >= 8 and not n7["trends"], f"{len(n7['missing']['FY2025'])} metrics missing")
# ================= REPORT =================
areas = ["MKT", "FIN", "THR", "COR", "ORC", "TWN", "MEM", "EVG", "OBS", "XF"]
print(f"{'Area':5s} {'Result':6s} Test"); print("-" * 110)
for ar, nm, ok, det in R: print(f"{ar:5s} {'PASS' if ok else 'FAIL':6s} {nm}" + ("" if ok else f"   ← {str(det)[:160]}"))
print("\nBY AREA: " + " · ".join(f"{a_} {sum(ok for x_, _, ok, _ in R if x_ == a_)}/{sum(1 for x_, *_ in R if x_ == a_)}" for a_ in areas))
n_ok = sum(ok for *_, ok, _ in [(r[0], r[1], r[2], r[3]) for r in R])
print(f"V7.1: {n_ok}/{len(R)} PASS")
json.dump([{"area": a_, "test": n, "pass": ok, "detail": str(d)[:300]} for a_, n, ok, d in R], open(f"{ROOT}/tests/last-v71-run.json", "w"), indent=1)
sys.exit(0 if n_ok == len(R) else 1)
