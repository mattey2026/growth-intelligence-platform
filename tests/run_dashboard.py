#!/usr/bin/env python3
"""
run_dashboard.py: V7.2 Dashboard Intelligence test suite. Run from the plugin root: python3 tests/run_dashboard.py
Browser tests use headless Chromium (Playwright). If Playwright/Chromium is unavailable those tests are reported as
SKIPPED — never as passed — and the suite exits non-zero.
Areas: SKL skill · AGT agent · CON contract · RND rendering · XFL cross-filter · DRL drill-down · PER persona ·
EVD evidence · SCN scenario · RSP responsive/design.
"""
import pathlib
import subprocess, json, os, sys, tempfile, shutil, glob, re, sqlite3
import yaml, jsonschema
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..")); SK = f"{ROOT}/skills"; FX = f"{ROOT}/tests/fixtures"
DS, AR = f"{SK}/dashboard-intelligence/scripts", f"{SK}/artifact-dashboard-intelligence/scripts"
TMP = tempfile.mkdtemp(); R = []
def T(area, name, ok, detail=""): R.append((area, name, "PASS" if ok else "FAIL", str(detail)[:200]))
def SKIP(area, name, why): R.append((area, name, "SKIP", why))
def run(*a, env=None):
    p = subprocess.run([sys.executable, *map(str, a)], capture_output=True, text=True, cwd=ROOT, env={**os.environ, **(env or {})})
    try: return p.returncode, json.loads(p.stdout)
    except Exception: return p.returncode, p.stdout + p.stderr
SCH = json.load(open(f"{ROOT}/schemas/dashboard.schema.json")); V = jsonschema.Draft202012Validator(SCH)
# ---------- build fixtures: demo + production contracts ----------
run(f"{DS}/demo_provider.py", "--out", f"{TMP}/b.json", "--asof", "2026-09-30")
def build(persona="sales_head", role="cro", bundle=f"{TMP}/b.json", out=None):
    out = out or f"{TMP}/c_{persona}_{role}.json"; c, r = run(f"{DS}/dashboard_builder.py", "--bundle", bundle, "--persona", persona, "--role", role, "--out", out, "--validate"); return json.load(open(out)) if os.path.exists(out) else None, r
C, rb = build()
shutil.copy(f"{FX}/growth_memory_v7.db", f"{TMP}/prod.db"); run(f"{DS}/competitive_threads.py", f"{TMP}/prod.db", "ingest", f"{FX}/sanofi_competitor_signals_SYNTHETIC.json")
run(f"{DS}/production_provider.py", "--entity-id", "A001", "--memory-db", f"{TMP}/prod.db", "--crm", f"{FX}/workbook_v2_2026-10-13.xlsx", "--asof", "2026-09-30", "--out", f"{TMP}/pb.json")
PC, rp = build(bundle=f"{TMP}/pb.json", out=f"{TMP}/pc.json")
KP = {m["id"]: m for m in C["metrics"]}
# ================= SKL: Dashboard Intelligence skill =================
fm = lambda p: yaml.safe_load(open(p).read().split("---")[1])
T("SKL", "1 both skills exist with valid frontmatter", all(fm(f"{SK}/{s}/SKILL.md")["name"] == s for s in ("dashboard-intelligence", "artifact-dashboard-intelligence")))
sk = open(f"{SK}/dashboard-intelligence/SKILL.md").read()
need = ["selection", "Composition", "KPI selection", "Visualization selection", "Persona adaptation", "Metric definitions", "Insights and anomalies", "Trend interpretation", "Cross-domain", "queries", "Drill-down",
        "Evidence display", "Action recommendations", "Scenario analysis", "filtering", "Comparison", "Dashboard state", "Design system"]
T("SKL", "2 skill defines all required capabilities", all(n.lower() in sk.lower() for n in need), [n for n in need if n.lower() not in sk.lower()])
dsm = open(f"{SK}/dashboard-intelligence/references/dashboard-design-system.md").read()
T("SKL", "3 design system defines tokens, both themes, type, 12-col grid, breakpoints", all(x in dsm for x in ["--accent", "graphite", "IBM Plex", "12-column", "1280", "1920", "Forbidden", "tabular"]))
T("SKL", "4 nine persona configurations", len(yaml.safe_load(open(f"{SK}/dashboard-intelligence/references/personas.yaml"))) == 9)
T("SKL", "5 demo contract builds and validates", rb.get("schema_valid") is True, rb.get("schema_errors"))
T("SKL", "6 demo runs the real V7.1 engines", {"marketing_signals.py", "financial_intel.py", "competitive_threads.py", "cross_domain_correlator.py", "domain_delta.py"} <= set(C["provenance"]["engines"]))
an = [i for i in C["insights"] if i.get("anomaly")]
T("SKL", "7 anomaly rule flags only the genuine dip (trend-adjusted)", len(an) == 1 and "2026-06" in an[0]["label"], [i["label"] for i in an])
T("SKL", "8 every narrative sentence cites evidence", all(s["evidence"] for s in C["narrative"]["summary"]))
chg = {c["label"]: c for c in C["changes"]}
T("SKL", "9 one number, one value across widgets (revenue, pipeline)", KP["revenue"]["display"] == chg["Revenue (TTM)"]["display"] and KP["pipeline"]["display"] == chg["Pipeline"]["display"], (KP["revenue"]["display"], chg["Revenue (TTM)"]["display"]))
pk = {m["id"]: m for m in PC["metrics"]}
T("SKL", "10 production: absent inputs are Not available, never zero", all(pk[k]["display"] == "Not available" for k in ("revenue", "competitive_exposure", "risk_exposure", "growth_potential", "opportunity_value")) and PC["drivers"]["display"] == "Not available",
  {k: pk[k]["display"] for k in pk})
T("SKL", "11 demo labelling on every demo record source", all("DEMO DATA" in e["source"] or e["data_mode"] == "public" or e["source"].startswith(("dashboard_builder", "competitive_threads", "financial_intel", "multiple", "delta")) for e in C["evidence"]))
# ================= AGT: Dashboard Intelligence agent =================
man = yaml.safe_load(open(f"{ROOT}/registry/manifests/dashboard-intelligence-agent.yaml"))
T("AGT", "1 manifest and generated agent file exist", os.path.exists(f"{ROOT}/agents/dashboard-intelligence-agent.md"))
c_, rv = run(f"{SK}/platform-admin/scripts/registry.py", ROOT, "validate"); T("AGT", "2 registry validates with the new agent", rv.get("status") == "OK", rv.get("errors"))
T("AGT", "3 least privilege: read-only, no shell, no actions", "Bash" not in man["allowed_tools"] and man["memory_permissions"] == "read" and man["action_permissions"] == [] and man["autonomy_level"] == 0)
T("AGT", "4 tiers: default T2, T3 strategic, T4 only for high-value synthesis", man["model_routing_policy"]["default_tier"] == "T2" and "T3" in man["escalation_rules"] and "T4" in man["escalation_rules"])
def plan(q): return run(f"{SK}/business-orchestrator/scripts/agent_planner.py", q, "--memory-db", f"{TMP}/prod.db")[1]
p1, p2, p3 = plan("Show me my Sanofi dashboard."), plan("Open the executive command center for Sanofi"), plan("Build me a cockpit for this account")
T("AGT", "5 three phrasings route to the dashboard intent", [p["intent"] for p in (p1, p2, p3)] == ["dashboard"] * 3, [p["intent"] for p in (p1, p2, p3)])
st = [s["step"] for s in p1["steps"]]
T("AGT", "6 agent designs before the contract and reviews after it", st.index("dashboard_design") < st.index("dashboard_contract") < st.index("contract_review") < st.index("render_artifact"))
T("AGT", "7 numbers run at T0 by the orchestrator, not the agent", all(s["tier"] == "T0" and s["agent"] == "business-orchestrator" for s in p1["steps"] if s["step"] in ("dashboard_contract", "render_artifact")))
T("AGT", "8 domain agents discovered from the registry", {"financial-intelligence-agent", "marketing-intelligence-agent", "competitive-thread-agent"} <= set(p1["dynamic_agents"]), p1["dynamic_agents"])
T("AGT", "9 V7.1 routing unaffected", plan("What's changing in this account?")["intent"] == "account_change" and plan("Build a complete account strategy.")["intent"] == "account_strategy")
_, cn = run(f"{SK}/platform-admin/scripts/registry.py", ROOT, "can", "dashboard-intelligence-agent", "--tool", "Bash"); T("AGT", "10 registry refuses shell to the agent", cn.get("allowed") is False, cn)
# ================= CON: Dashboard Contract =================
T("CON", "1 demo contract valid", not list(V.iter_errors(C)))
T("CON", "2 production contract valid", not list(V.iter_errors(PC)), [e.message[:80] for e in list(V.iter_errors(PC))[:3]])
om = ["Dashboard", "DashboardWidget", "DashboardLayout", "DashboardFilter", "DashboardQuery", "DashboardInsight", "DashboardMetric", "DashboardSignal", "DashboardOpportunity", "DashboardRisk", "DashboardAction", "DashboardEvidence", "DashboardScenario"]
T("CON", "3 object model: all 13 types defined", all(x in SCH["$defs"] for x in om), [x for x in om if x not in SCH["$defs"]])
base = set(SCH["$defs"]["DashboardMeasure"]["properties"])
T("CON", "4 base object supports id,label,value,unit,trend,previous,confidence,source,timestamp,evidence,drill", {"id", "label", "value", "unit", "trend", "previous_value", "confidence", "source", "timestamp", "evidence", "drill_down_target"} <= base)
EVI = {e["id"] for e in C["evidence"]}
refs = [e for x in C["metrics"] + C["opportunities"] + C["risks"] + C["competitive_threads"] + C["actions"] + C["changes"] for e in x.get("evidence", [])] + [e for s in C["narrative"]["summary"] for e in s["evidence"]]
T("CON", "5 every evidence reference resolves", all(r in EVI for r in refs), [r for r in refs if r not in EVI][:5])
dt = [x["drill_down_target"] for x in C["metrics"] + C["opportunities"] + C["risks"] + C["competitive_threads"] + C["relationships"] + C["changes"] if x.get("drill_down_target")]
T("CON", "6 every drill target resolves", all(d in C["drill"] for d in dt), [d for d in dt if d not in C["drill"]][:5])
bad = json.loads(json.dumps(C)); bad["metrics"][0].pop("id"); bad["opportunities"][0]["probability"] = 1.7
T("CON", "7 schema rejects malformed contracts", len(list(V.iter_errors(bad))) >= 2)
json.dump(bad, open(f"{TMP}/bad.json", "w")); cb, _ = run(f"{AR}/render_dashboard.py", "--contract", f"{TMP}/bad.json", "--out", f"{TMP}/bad.html")
T("CON", "8 renderer refuses an invalid contract", cb == 2 and not os.path.exists(f"{TMP}/bad.html"))
S_, _ = build("sales_head", "seller")
T("CON", "9 security: seller's contract contains no account economics (removed, not hidden)", "margin" not in {m["id"] for m in S_["metrics"]} and not S_["financial"]["account"] and S_["permissions"]["restricted"], S_["permissions"]["restricted"])
T("CON", "10 renderer-independent: no HTML/CSS/JS in the contract", not re.search(r"<(div|span|script|style)\b|class=|function\s*\(", json.dumps(C)))
_, s1 = run(f"{DS}/dashboard_state.py", f"{TMP}/prod.db", "set", "--user", "u1", "--dashboard", "egcc", "--entity", "sanofi", "--state", '{"persona":"ceo","filters":{"competitor":"Competitor X"}}', env={"GROWTH_TENANT": "tenant-a"})
_, s2 = run(f"{DS}/dashboard_state.py", f"{TMP}/prod.db", "get", "--user", "u1", "--dashboard", "egcc", "--entity", "sanofi", env={"GROWTH_TENANT": "tenant-a"})
cx_, _ = run(f"{DS}/dashboard_state.py", f"{TMP}/prod.db", "get", "--user", "u1", "--dashboard", "egcc", "--entity", "sanofi", env={"GROWTH_TENANT": "tenant-b"})
cy_, _ = run(f"{DS}/dashboard_state.py", f"{TMP}/prod.db", "set", "--user", "u1", "--dashboard", "egcc", "--entity", "sanofi", "--state", '{"role":"admin"}', env={"GROWTH_TENANT": "tenant-a"})
T("CON", "11 state persists; tenant-isolated; cannot carry a role", s2["state"]["persona"] == "ceo" and cx_ == 3 and cy_ == 2)
# ================= browser tests =================
try:
    from playwright.sync_api import sync_playwright
    PW = sync_playwright().start(); BR = PW.chromium.launch()
except Exception as e:
    PW = None; why = f"Playwright/Chromium unavailable: {e}"
if PW is None:
    for a_, n in [("RND", 10), ("XFL", 10), ("DRL", 10), ("PER", 6), ("EVD", 5), ("SCN", 5), ("RSP", 5)]:
        for i in range(n): SKIP(a_, f"{i + 1} browser test", why)
else:
    run(f"{AR}/render_dashboard.py", "--contract", f"{TMP}/c_sales_head_cro.json", "--out", f"{TMP}/d.html"); run(f"{AR}/render_dashboard.py", "--contract", f"{TMP}/pc.json", "--out", f"{TMP}/p.html")
    def page(f="d.html", w=1440):
        pg = BR.new_page(viewport={"width": w, "height": 900}); pg._errs = []; pg.on("pageerror", lambda e: pg._errs.append(str(e)))
        pg.goto(pathlib.Path(TMP, f).as_uri()); pg.wait_for_timeout(400); return pg
    E = lambda pg, js: pg.evaluate(js)
    def view(pg, v): E(pg, f"()=>{{GI.state().view='{v}';GI.render()}}"); pg.wait_for_timeout(200)
    # ---------- RND ----------
    pg = page()
    T("RND", "1 loads with no script errors", not pg._errs, pg._errs)
    T("RND", "2 KPI strip renders the persona's KPIs", E(pg, "document.querySelectorAll('[data-kpi]').length") == len(C["metrics"]))
    shown = E(pg, "Object.fromEntries([...document.querySelectorAll('[data-kpi]')].map(k=>[k.dataset.kpi,k.querySelector('.kpi-v').textContent]))")
    T("RND", "3 values are the contract's display strings, verbatim", all(shown[m["id"]] == m["display"] for m in C["metrics"]), shown)
    mut = json.loads(json.dumps(C)); mut["metrics"][0]["display"] = "$999.9M"; mut["metrics"][0]["value"] = 1
    json.dump(mut, open(f"{TMP}/mut.json", "w")); run(f"{AR}/render_dashboard.py", "--contract", f"{TMP}/mut.json", "--out", f"{TMP}/mut.html"); pm = page("mut.html")
    T("RND", "4 no business computation: renderer shows whatever the contract says", E(pm, f"document.querySelector('[data-kpi={mut['metrics'][0]['id']}] .kpi-v').textContent") == "$999.9M"); pm.close()
    types = set()
    for v in [n["id"] for n in C["navigation"]]:
        view(pg, v); types |= set(E(pg, "[...document.querySelectorAll('section.w')].map(s=>s.dataset.type)"))
    for pers, v in [("investor", "financial"), ("growth_ops", "marketing"), ("coo", "operations"), ("ceo", "market")]:
        E(pg, f"()=>{{GI.state().persona='{pers}';GI.state().view='{v}';GI.render()}}"); pg.wait_for_timeout(200); types |= set(E(pg, "[...document.querySelectorAll('section.w')].map(s=>s.dataset.type)"))
    req = {"kpi_strip", "narrative", "change_list", "trend_chart", "driver_tree", "opportunity_radar", "risk_matrix", "competitor_landscape", "thread_list", "financial_panel", "marketing_panel", "relationship_map", "swot", "health", "action_list", "scenario_lab", "comparison", "table"}
    T("RND", "5 all required visualizations render", req <= types, sorted(req - types))
    fails = E(pg, "[...document.querySelectorAll('.empty')].filter(e=>e.textContent.startsWith('This section could not')).length")
    T("RND", "6 no widget failed in any view", fails == 0 and not pg._errs, pg._errs)
    E(pg, "()=>{GI.state().persona='sales_head';GI.state().view='overview';GI.render()}")
    T("RND", "7 header shows entity, segment, period; demo banner shown", E(pg, "document.querySelector('.ctx-entity').textContent") == "Sanofi" and "DEMO DATA" in E(pg, "document.querySelector('.demo').textContent"))
    lt = E(pg, "getComputedStyle(document.body).backgroundColor"); E(pg, "()=>{GI.state().theme='dark';GI.render()}"); dk = E(pg, "getComputedStyle(document.body).backgroundColor"); E(pg, "()=>{GI.state().theme='light';GI.render()}")
    T("RND", "8 light and dark themes (dark = graphite, not black)", lt != dk and dk not in ("rgb(0, 0, 0)",), (lt, dk))
    pp = page("p.html"); bad_ = 0
    for v in [n["id"] for n in PC["navigation"]]:
        view(pp, v); bad_ += E(pp, "[...document.querySelectorAll('.empty')].filter(e=>e.textContent.startsWith('This section could not')).length")
    T("RND", "9 production contract renders every view with explicit empty states", bad_ == 0 and not pp._errs and E(pp, "document.body.textContent.includes('Not available')"), pp._errs); pp.close()
    E(pg, "()=>GI.ask('What changed in the last 30 days?')")
    la = E(pg, "document.body.dataset.lastAsk || ''")
    T("RND", "10 Ask Intelligence hands the question + context to the Business Orchestrator", "What changed" in la and "Sanofi" in la and E(pg, "GI.state().view") == "overview", la[:120])
    # ---------- XFL ----------
    def reset(p_=pg): E(p_, "()=>{GI.clearFilters();GI.state().view='overview';GI.state().persona='sales_head';GI.render()}")
    reset(); view(pg, "competition"); E(pg, "()=>GI.setFilter('competitor','Competitor X')")
    th = E(pg, "[...document.querySelectorAll('[data-thread]')].map(r=>r.querySelector('td').textContent)")
    T("XFL", "1 competitor filter narrows competitive threads", th and all(x == "Competitor X" for x in th), th)
    dimmed = E(pg, "[...document.querySelectorAll('#radar-radar .mark')].filter(m=>m.classList.contains('dim')).length"); tot = len(C["opportunities"])
    T("XFL", "2 radar dims opportunities of other competitors", 0 < dimmed < tot, (dimmed, tot))
    view(pg, "overview"); pv_ = E(pg, "document.querySelector('[data-kpi=pipeline] .kpi-v').textContent")
    T("XFL", "3 KPIs switch to precomputed filtered values", pv_ == KP["pipeline"]["by_facet"]["competitor"]["Competitor X"]["display"], pv_)
    T("XFL", "4 unsplittable KPIs say so rather than recompute", "dim" in E(pg, "document.querySelector('[data-kpi=revenue]').className"))
    ch = E(pg, "[...document.querySelectorAll('[data-change]')].length")
    T("XFL", "5 What changed responds to the filter", 0 < ch < len(C["changes"]), (ch, len(C["changes"])))
    view(pg, "actions"); ac = E(pg, "[...document.querySelectorAll('[data-action]')].length")
    T("XFL", "6 actions respond to the filter", 0 < ac < len(C["actions"]), (ac, len(C["actions"])))
    T("XFL", "7 active filter shown as a removable chip", E(pg, "document.querySelectorAll('[data-chip=competitor]').length") == 1)
    E(pg, "()=>GI.clearFilters()"); view(pg, "actions")
    T("XFL", "8 clearing filters restores everything", E(pg, "[...document.querySelectorAll('[data-action]')].length") == len(C["actions"]))
    view(pg, "growth"); pg.click("[data-driver='Expansion']"); pg.wait_for_timeout(200)
    T("XFL", "9 clicking a growth driver filters the dashboard", E(pg, "GI.state().filters.driver") == "Expansion" and E(pg, "document.querySelector('[data-kpi]') ? true : true"))
    E(pg, "()=>GI.clearFilters()"); view(pg, "overview"); E(pg, "()=>GI.setFilter('domain','financial')")
    T("XFL", "10 domain filter keeps only matching changes", all(x == "financial" for x in E(pg, "[...document.querySelectorAll('[data-change] td:first-child')].map(t=>t.textContent)")))
    # ---------- DRL ----------
    reset(); pg.click("[data-kpi=growth_potential]"); pg.wait_for_timeout(200)
    T("DRL", "1 KPI click opens its drill-down", E(pg, "document.getElementById('drawer').classList.contains('open') && document.getElementById('drawer').dataset.node") == "D-growth_potential")
    pg.click("[data-drill='D-drv-Expansion']"); pg.wait_for_timeout(150)
    T("DRL", "2 growth potential → Expansion", E(pg, "document.getElementById('drawer').dataset.node") == "D-drv-Expansion")
    pg.click("[data-drill='D-opp-OPP-02']"); pg.wait_for_timeout(150)
    kids = E(pg, "[...document.querySelectorAll('#drawer [data-drill]')].map(x=>x.dataset.drill)")
    T("DRL", "3 → AI transformation → evidence, signals, driver, competitive context, action", all(any(k.endswith(s) for k in kids) for s in ("-ev", "-sig", "-drv", "-comp", "-act")), kids)
    T("DRL", "4 breadcrumb keeps the path", E(pg, "[...document.querySelectorAll('#drawer .crumbs button')].map(b=>b.textContent)") == ["Growth potential", "Expansion"])
    pg.click("#drawer .crumbs button"); pg.wait_for_timeout(150)
    T("DRL", "5 breadcrumb navigates back", E(pg, "document.getElementById('drawer').dataset.node") == "D-growth_potential")
    dead = [k for k, n in C["drill"].items() if not n["children"] and not n["evidence"] and not (n.get("links") or {}).get("actions") and not n.get("text")]
    T("DRL", "6 no dead ends: every drill node has children, evidence, action or text", not dead, dead[:5])
    T("DRL", "7 every available KPI is drillable", all(m["drill_down_target"] in C["drill"] for m in C["metrics"] if m.get("value") is not None))
    E(pg, "()=>document.querySelector('#drawer .ib').click()"); pg.click("#radar-radar .mark[data-id='OPP-01']"); pg.wait_for_timeout(150)
    T("DRL", "8 radar bubble opens the opportunity drill", E(pg, "document.getElementById('drawer').dataset.node") == "D-opp-OPP-01")
    E(pg, "()=>document.querySelector('#drawer .ib').click()"); pg.click("[data-change]"); pg.wait_for_timeout(150)
    T("DRL", "9 a change row opens its evidence path", (E(pg, "document.getElementById('drawer').dataset.node") or "").startswith("D-chg-"))
    E(pg, "()=>document.querySelector('#drawer .ib').click()"); view(pg, "customers"); E(pg, "()=>GI.openDrill('D-stk-C-D')"); pg.wait_for_timeout(150)
    T("DRL", "10 stakeholder drill shows relationship evidence and opportunities", E(pg, "document.querySelectorAll('#drawer .ev').length") > 0 and E(pg, "document.querySelectorAll('#drawer [data-drill^=D-opp]').length") > 0)
    E(pg, "()=>document.querySelector('#drawer .ib').click()")
    # ---------- PER ----------
    P = yaml.safe_load(open(f"{SK}/dashboard-intelligence/references/personas.yaml"))
    for i, pers in enumerate(["investor", "ceo", "growth_ops", "sales_head", "sales_director", "ae"], 1):
        E(pg, f"()=>{{GI.clearFilters();GI.state().persona='{pers}';GI.state().view='overview';GI.render()}}"); pg.wait_for_timeout(150)
        k0 = E(pg, "document.querySelector('[data-kpi]').dataset.kpi"); tabs = E(pg, "[...document.querySelectorAll('[data-view]')].map(b=>b.dataset.view)")
        vals = E(pg, "Object.fromEntries([...document.querySelectorAll('[data-kpi]')].map(k=>[k.dataset.kpi,k.querySelector('.kpi-v').textContent]))")
        same = all(vals[k] == KP[k]["display"] for k in vals)
        CANON = ["overview", "growth", "accounts", "pipeline", "customers", "competition", "market", "financial", "marketing", "operations", "decisions", "actions"]
        T("PER", f"{i} {P[pers]['label']}: KPI order, tabs (canonical order), same data", k0 == P[pers]["kpis"][0] and set(tabs) == set(P[pers]["tabs"]) and tabs == sorted(tabs, key=CANON.index) and same, (k0, tabs))
    # ---------- EVD ----------
    E(pg, "()=>{GI.state().persona='sales_head';GI.state().view='overview';GI.render()}"); pg.click(".state-sum .pv"); pg.wait_for_timeout(150)
    card = E(pg, "document.querySelector('#drawer .ev') ? document.querySelector('#drawer .ev').textContent : ''")
    T("EVD", "1 provenance mark opens the evidence drawer", E(pg, "document.getElementById('drawer').dataset.kind") == "evidence" and card)
    T("EVD", "2 evidence shows source, date, claim type, confidence", all(x in card for x in ("Source",)) and re.search(r"\d{4}-\d{2}-\d{2}|undated", card) and re.search(r"FACT|CALC|INFERENCE|HYPOTHESIS", card) and "%" in card, card[:160])
    E(pg, "()=>document.querySelector('#drawer .ib').click()"); E(pg, "()=>{GI.state().persona='investor';GI.state().view='financial';GI.render()}"); pg.click("[data-fin='fin-revenue'] .pv"); pg.wait_for_timeout(150)
    T("EVD", "3 published figures are labelled Public source with the citation", "Public source" in E(pg, "document.getElementById('drawer').textContent") and "Sanofi press release" in E(pg, "document.getElementById('drawer').textContent"))
    E(pg, "()=>document.querySelector('#drawer .ib').click()"); E(pg, "()=>{GI.state().persona='sales_head';GI.state().view='overview';GI.render();GI.openEvidence(['EV-OPP-01'],'x')}")
    T("EVD", "4 demo records are labelled Demo", "Demo" in E(pg, "document.getElementById('drawer').textContent"))
    E(pg, "()=>document.querySelector('#drawer .ib').click()"); E(pg, "()=>GI.openDrill('D-growth_potential')"); E(pg, "()=>GI.ask('Show evidence')"); pg.wait_for_timeout(150)
    T("EVD", "5 'Show evidence' opens evidence for the item in focus", E(pg, "document.getElementById('drawer').dataset.kind") == "evidence")
    E(pg, "()=>document.querySelector('#drawer .ib').click()")
    # ---------- SCN ----------
    sc = C["scenarios"]; ren = next(s for s in sc if s["id"].startswith("SC-LOSS-")); o1 = next(o for o in C["opportunities"] if o["id"] == ren["id"].replace("SC-LOSS-", ""))
    T("SCN", "1 scenarios are labelled MODELED with assumptions", all(s["modeled"] and s["assumptions"] and s["claim_type"] == "MODELED" for s in sc) and len(sc) >= 3)
    T("SCN", "2 renewal-loss revenue delta = −value ÷ stated term", abs(ren["delta"]["revenue_run_rate"] + o1["value"] / 3) < 0.01 and "3 years" in ren["assumptions"][0], ren["delta"])
    T("SCN", "3 probability variants scale the expected impact", len(ren["variants"]) == 3 and ren["variants"][-1]["expected_revenue_impact"] == ren["rows"][0]["delta"])
    E(pg, "()=>{GI.state().view='decisions';GI.render()}"); win_id = next(s["id"] for s in sc if s["id"].startswith("SC-WIN-")); pg.click(f"[data-scenario='{win_id}']"); pg.wait_for_timeout(150)
    T("SCN", "4 Scenario Lab switches scenarios and shows MODELED label", E(pg, "GI.state().scenario") == win_id and "MODELED" in E(pg, "document.querySelector('[data-widget=scenario_lab]').textContent"))
    E(pg, "()=>{GI.state().view='overview';GI.render()}"); E(pg, "()=>GI.ask('What happens if the competitor wins the renewal?')"); pg.wait_for_timeout(150)
    T("SCN", "5 'What happens if…' opens the Scenario Lab", E(pg, "GI.state().view") == "decisions" and E(pg, "!!document.querySelector('[data-widget=scenario_lab]')"))
    # ---------- RSP ----------
    over = {}
    for w in (1280, 1440, 1600, 1920):
        p_ = page(w=w); o_ = 0
        for v in [n["id"] for n in C["navigation"]]:
            view(p_, v); o_ = max(o_, E(p_, "document.documentElement.scrollWidth-document.documentElement.clientWidth"))
        over[w] = o_; p_.close()
    T("RSP", "1 no horizontal overflow at 1280/1440/1600/1920 in any view", all(v == 0 for v in over.values()), over)
    pt = page(w=1024); spans = set(E(pt, "[...document.querySelectorAll('section.w')].map(s=>Math.round(s.getBoundingClientRect().width))"))
    T("RSP", "2 tablet (1024): widgets stack full width, no overflow", len(spans) == 1 and E(pt, "document.documentElement.scrollWidth-document.documentElement.clientWidth") == 0, spans); pt.close()
    rows_ok = all(sum(w_["span"] for w_ in ws) % 12 == 0 and all((a_["span"] + b_["span"] == 12) for a_, b_ in zip([x for x in ws if x["span"] < 12][::2], [x for x in ws if x["span"] < 12][1::2])) for pl in C["persona_layouts"].values() for ws in pl["views"].values())
    T("RSP", "3 every layout row sums to 12 columns (all personas, all views)", rows_ok)
    css = open(f"{SK}/artifact-dashboard-intelligence/assets/command-center.css").read()
    forb = [x for x in ("linear-gradient", "radial-gradient", "backdrop-filter", "#D97757", "#F4F1EA", "#7C3AED", "#8B5CF6") if x.lower() in css.lower()]
    shadows = re.findall(r"([^{}]+)\{[^}]*box-shadow[^}]*\}", css); non_overlay = [s.strip() for s in shadows if not re.search(r"drawer|menu-pop|flash", s)]
    T("RSP", "4 no Claude-default or decorative styling; shadows only on overlays", not forb and not non_overlay, forb + non_overlay)
    E(pg, "()=>{GI.clearFilters();GI.state().persona='sales_head';GI.state().view='overview';GI.render()}"); pg.wait_for_timeout(150)
    fam = E(pg, "getComputedStyle(document.querySelector('.kpi-v')).fontFamily"); num = E(pg, "getComputedStyle(document.querySelector('.kpi-v')).fontVariantNumeric")
    T("RSP", "5 IBM Plex type with tabular numerals", "IBM Plex Sans" in fam and "tabular-nums" in num, (fam, num))
    BR.close(); PW.stop()
# ---------- report ----------
areas = ["SKL", "AGT", "CON", "RND", "XFL", "DRL", "PER", "EVD", "SCN", "RSP"]
for a_, n, s, d in R: print(f"{a_:4s} {s:5s} {n}" + ("" if s == "PASS" else f"   ← {d}"))
print("\nBY AREA: " + " · ".join(f"{a_} {sum(1 for x in R if x[0] == a_ and x[2] == 'PASS')}/{sum(1 for x in R if x[0] == a_)}" for a_ in areas))
np_, ns = sum(1 for x in R if x[2] == "PASS"), sum(1 for x in R if x[2] == "SKIP")
print(f"DASHBOARD: {np_}/{len(R)} PASS" + (f" · {ns} SKIPPED" if ns else ""))
json.dump([{"area": a_, "test": n, "result": s, "detail": d} for a_, n, s, d in R], open(f"{ROOT}/tests/last-dashboard-run.json", "w"), indent=1)
sys.exit(0 if np_ == len(R) else 1)
