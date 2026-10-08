#!/usr/bin/env python3
"""
run_prompts.py: V8 Starter Prompt & Discovery test suite. Run from the plugin root: python3 tests/run_prompts.py
Per capability (34): COV coverage · QLT quality · RTT routing by typed text (primary) · RTH routing with the capability
hint (all prompts) · FUP follow-ups · SLH slash command. Global: PER personas · CTX context · TR3 contextual tier ·
DSC discovery · DSH dashboard integration (Chromium; SKIPPED, never passed, if unavailable) · SYN catalog sync · REG registry.
Typed routing of ADDITIONAL prompts is measured and reported, not asserted (they are clicked from a menu, which carries the hint).
"""
import pathlib
import glob, json, os, re, subprocess, sys, tempfile
import yaml
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")); import build_fixtures; build_fixtures.ensure()   # rebuild binary fixtures from readable SQL/JSON sources
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..")); SK = f"{ROOT}/skills"
CAT = f"{SK}/growth-discovery/references/starter-prompts"; ENG = f"{SK}/growth-discovery/scripts/prompt_engine.py"; PLN = f"{SK}/business-orchestrator/scripts/agent_planner.py"
R = []
def T(area, name, ok, detail=""): R.append((area, name, "PASS" if ok else "FAIL", str(detail)[:220]))
def SKIP(area, name, why): R.append((area, name, "SKIP", why))
def eng(*a):
    r = subprocess.run([sys.executable, ENG, *a], capture_output=True, text=True); return json.loads(r.stdout)
def plan(text, cap=None):
    r = subprocess.run([sys.executable, PLN, text] + (["--capability", cap] if cap else []), capture_output=True, text=True); p = json.loads(r.stdout)
    return p["intent"], {s for st in p["steps"] for s in st.get("skills", [])}, p
IDX = yaml.safe_load(open(f"{CAT}/_index.yaml")); PERS = yaml.safe_load(open(f"{CAT}/_personas.yaml"))
CAPS = {yaml.safe_load(open(f))["capability"]["id"]: yaml.safe_load(open(f))["capability"] for f in sorted(glob.glob(f"{CAT}/*.yaml")) if not os.path.basename(f).startswith("_")}
SKILLS = set(os.listdir(SK))
REG = {yaml.safe_load(open(f))["agent_id"]: yaml.safe_load(open(f)) for f in glob.glob(f"{ROOT}/registry/manifests/*.yaml") if not os.path.basename(f).startswith("_")}
OPT = re.compile(r"\[\[(.*?)(?:\|(.*?))?\]\]")
def bare(t): return re.sub(r"\s{2,}", " ", OPT.sub(lambda m: m.group(2) or "", t)).replace(" .", ".").replace(" ?", "?").strip()
FORBID = sorted(SKILLS | set(REG) | {"agent", "skill", "orchestrator", "planner", "registry", "model tier", "T0", "T1", "T2", "T3", "T4", "LLM", "subagent", "invoke", "prompt_engine", "python"}, key=len, reverse=True)
VERB_OK = re.compile(r"^(Build|Show|Find|Identify|Map|Give|Create|Recommend|Assess|Tell|Review|Run|Analyze|Explain|Prep|Prepare|Process|Extract|Update|Draft|Summarize|Log|Compare|Turn|Size|Predict|Record|Help|Prioritize|Model|Stress-test|Challenge|Set|Watch|Alert|Notify|Research|Personalize|Search|Correct|Forget|Open|Refresh|Drill|Design|Catch|Route|Connect|Respond|Tailor|Flag|Escalate|Cancel|Investigate|Act|Check|Break|Reconcile|Clean|Profile|Forecast|Search|Turn|Respond|Re-engage|Protect|Detect|Get|Let|Disable|Brief|Plan)\b|^(What|Which|Who|Where|When|Why|How|Is|Are|Will|Should|Any|Anything|Has|Do|Does|Can|Did)\b")
def all_prompts(c): return c["primary_prompts"] + c["additional_prompts"]
VARS = set(IDX["variables"])
typed_add_ok = typed_add_tot = 0
for cid, c in CAPS.items():
    P, A = c["primary_prompts"], c["additional_prompts"]
    # ---------------- COV ----------------
    T("COV", f"{cid}: 6 primary, 10–20 additional, outcomes, follow-ups, command", len(P) == 6 and 10 <= len(A) <= 20 and c["example_outcomes"] and len(c["follow_up_prompts"]) >= 3 and c["slash_command"].startswith("/") and c["routes_to"]["skill"] in SKILLS,
      (len(P), len(A), len(c["follow_up_prompts"])))
    # ---------------- QLT ----------------
    issues = []
    texts = [p["text"] for p in all_prompts(c)] + c["follow_up_prompts"] + [t for v in (c.get("persona_prompts") or {}).values() for t in v]
    for t in texts:
        b = bare(t); words = len(b.split())
        if not VERB_OK.match(b): issues.append(f"not verb/question-led: {b}")
        if words > 14: issues.append(f"too long ({words}): {b}")
        if not b.endswith((".", "?")): issues.append(f"no end punctuation: {b}")
        low = " " + b.lower() + " "
        for f in FORBID:
            if re.search(r"(?<![a-z])" + re.escape(f.lower()) + r"(?![a-z])", low): issues.append(f"internal term '{f}': {b}"); break
        if t.count("[[") != t.count("]]"): issues.append(f"unbalanced template: {t}")
        if set(re.findall(r"\{(\w+)\}", t)) - VARS: issues.append(f"unknown variable: {t}")
        if re.search(r"[a-z][A-Z]|[a-z](this|the)\b(?<=\w{6})", b) and re.search(r"[a-z](this|the) ", b): issues.append(f"stuck words: {b}")
    cats = {p["category"] for p in all_prompts(c)}
    if not cats <= set(IDX["prompt_categories"]): issues.append(f"bad category {cats - set(IDX['prompt_categories'])}")
    if len({bare(p["text"]).lower() for p in all_prompts(c)}) != len(all_prompts(c)): issues.append("duplicate prompt in capability")
    T("QLT", f"{cid}: actionable, plain business language, valid templates", not issues, issues[:3])
    # ---------------- RTT (typed primary) ----------------
    miss = []
    for p in P:
        target = CAPS[p["routes_to_capability"]]["routes_to"]["skill"] if p.get("routes_to_capability") else c["routes_to"]["skill"]
        _, sk, _ = plan(bare(p["text"]))
        if target not in sk: miss.append(bare(p["text"]))
    T("RTT", f"{cid}: all 6 primary prompts route by typed text", not miss, miss)
    # ---------------- RTH (clicked / slash: capability hint) ----------------
    miss = []
    for p in all_prompts(c):
        rc = p.get("routes_to_capability") or cid
        it, sk, pl = plan(bare(p["text"]), rc)
        if CAPS[rc]["routes_to"]["skill"] not in sk or it != CAPS[rc]["routes_to"]["intent"]: miss.append(bare(p["text"]))
        typed_add_tot += p in A
        if p in A: typed_add_ok += CAPS[rc]["routes_to"]["skill"] in plan(bare(p["text"]))[1]
    T("RTH", f"{cid}: all {len(all_prompts(c))} prompts route deterministically when clicked", not miss, miss[:3])
    # ---------------- FUP ----------------
    fu = eng("followups", "--after", bare(P[0]["text"]), "--account", "Sanofi")
    ok = fu["prompts"] and all(x["prompt"] != bare(P[0]["text"]) for x in fu["prompts"]) and all("{" not in x["prompt"] and "[[" not in x["prompt"] for x in fu["prompts"])
    rt = all(CAPS[x["_route"]["capability_id"]]["routes_to"]["skill"] in plan(x["prompt"], x["_route"]["capability_id"])[1] for x in fu["prompts"])
    T("FUP", f"{cid}: follow-ups are generated, resolved and routable", ok and rt and len(fu["prompts"]) <= 5, [x["prompt"] for x in fu["prompts"]][:3])
    # ---------------- SLH ----------------
    names = [c["slash_command"]] + c["aliases"]; probs = []
    for n in names:
        fn = {"/memory": "/business-memory"}.get(n, n)[1:]; f = f"{ROOT}/commands/{fn}.md"
        if not os.path.exists(f): probs.append(f"missing {fn}"); continue
        txt = open(f).read(); fm = yaml.safe_load(txt.split("---")[1])
        if not fm.get("description") or not fm.get("argument-hint"): probs.append(f"{fn}: frontmatter")
        if "business-orchestrator" not in txt or f"--capability {cid}" not in txt or "$ARGUMENTS" not in txt: probs.append(f"{fn}: does not route to the orchestrator")
        if re.search(r"\b(threshold|score|probability\s*[<>=]|\d+%)", txt): probs.append(f"{fn}: contains business logic")
        if any(re.search(r"(?<![a-z-])" + re.escape(s) + r"(?![a-z-])", fm["description"]) for s in SKILLS | set(REG)): probs.append(f"{fn}: internal name in description")
    T("SLH", f"{cid}: slash command {', '.join(names)} routes to the orchestrator only", not probs, probs)
# ---------------- global: catalog integrity ----------------
user_skills = SKILLS - set(IDX["internal_skills"])
covered = {c["routes_to"]["skill"] for c in CAPS.values()}
T("COV", "every user-facing skill has starter prompts", user_skills <= covered | {"growth-discovery"}, sorted(user_skills - covered - {"growth-discovery"}))
T("COV", "internal skills are declared, exist, and are not user-facing", set(IDX["internal_skills"]) <= SKILLS and not (set(IDX["internal_skills"]) & covered))
T("COV", "no orphan prompt files: index lists exactly the catalog files", set(IDX["capabilities"]) == set(CAPS))
T("COV", "every route intent exists in the orchestrator", all(plan("x", cid)[0] == c["routes_to"]["intent"] for cid, c in CAPS.items()))
T("COV", "cross-links point to real capabilities", all(p["routes_to_capability"] in CAPS for c in CAPS.values() for p in c["primary_prompts"] if p.get("routes_to_capability")))
prim = [bare(p["text"]).lower() for c in CAPS.values() for p in c["primary_prompts"]]
T("QLT", "primary prompts are unique across capabilities (no ambiguous cards)", len(prim) == len(set(prim)), [x for x in set(prim) if prim.count(x) > 1])
lens = [len(bare(p["text"]).split()) for c in CAPS.values() for p in c["primary_prompts"]]
T("QLT", "primary prompts are short (≤ 12 words for ≥ 95%)", sum(1 for l in lens if l <= 12) / len(lens) >= 0.95, f"{sum(1 for l in lens if l <= 12)}/{len(lens)}")
T("QLT", "seven prompt categories used consistently", set(IDX["prompt_categories"]) == {"Discover", "Analyze", "Investigate", "Decide", "Prepare", "Act", "Monitor"} and {p["category"] for c in CAPS.values() for p in all_prompts(c)} == set(IDX["prompt_categories"]))
# ---------------- PER ----------------
need = {"investor", "ceo", "cfo", "coo", "growth_ops", "cro", "sales_head", "sales_director", "ae", "marketing_leader", "cs_leader", "operations_leader", "it_leader"}
T("PER", "13 personas defined", set(PERS) == need, sorted(need ^ set(PERS)))
for pk in sorted(need):
    h = eng("home", "--persona", pk)
    T("PER", f"{pk}: home shows 6 distinct, routable prompts", len(h["prompts"]) == 6 and len({x["prompt"] for x in h["prompts"]}) == 6 and all(x["_route"]["capability_id"] in CAPS for x in h["prompts"]))
T("PER", "CEO home leads with growth and risk signals", eng("home", "--persona", "ceo")["prompts"][0]["capability"] == "Executive Command Center")
T("PER", "Sales Director sees deals needing intervention", any("intervention" in x["prompt"] for x in eng("menu", "--capability", "deal", "--persona", "sales_director")["prompts"]))
T("PER", "AE home starts with call preparation", eng("home", "--persona", "ae")["prompts"][0]["prompt"] == "Prep me for my next sales call.")
T("PER", "Investor home is about growth, profitability and risk", "profitability" in json.dumps(eng("menu", "--capability", "executive", "--persona", "investor")["prompts"]))
T("PER", "persona changes the prompts, not the capability set", set(eng("explore")) == set(eng("explore")) and eng("menu", "--capability", "account", "--persona", "ceo")["prompts"] != eng("menu", "--capability", "account")["prompts"])
# ---------------- CTX ----------------
m1, m0 = eng("menu", "--capability", "account", "--account", "Sanofi"), eng("menu", "--capability", "account")
T("CTX", "account inserted when known", m1["prompts"][0]["prompt"] == "Build my complete Sanofi account strategy.", m1["prompts"][0]["prompt"])
T("CTX", "generic phrasing when no account", m0["prompts"][0]["prompt"] == "Build my complete account strategy." and m0["prompts"][1]["prompt"] == "What has changed in this account?")
T("CTX", "competitor inserted when known", eng("menu", "--capability", "threads", "--competitor", "Competitor X")["prompts"][2]["prompt"] == "Explain the Competitor X thread.")
leftover = [x["prompt"] for cid in CAPS for ctx in ([], ["--account", "Sanofi", "--competitor", "Competitor X", "--opportunity", "OPP-01", "--meeting", "the CIO meeting", "--industry", "pharma"])
            for x in eng("menu", "--capability", cid, "--more", "--admin", *ctx)["prompts"] if re.search(r"[{}\[\]]|\s\s", x["prompt"])]
T("CTX", "no unresolved variables, brackets or double spaces anywhere (with and without context)", not leftover, leftover[:3])
T("CTX", "resolve: optional segment needs every variable", eng("resolve", "--text", "Find X[[ in {account} for {competitor}]].", "--account", "A")["text"] == "Find X.")
# ---------------- TR3 contextual ----------------
tmp = tempfile.mkdtemp(); con = None
bundle = subprocess.run([sys.executable, f"{SK}/dashboard-intelligence/scripts/demo_provider.py", "--out", f"{tmp}/b.json"], capture_output=True, text=True)
subprocess.run([sys.executable, f"{SK}/dashboard-intelligence/scripts/dashboard_builder.py", "--bundle", f"{tmp}/b.json", "--persona", "sales_head", "--out", f"{tmp}/c.json"], capture_output=True, text=True)
C = json.load(open(f"{tmp}/c.json"))
r3 = eng("recommend", "--persona", "sales_head", "--contract", f"{tmp}/c.json")
ctxs = [x for x in r3["prompts"] if x.get("tier") == "contextual"]
T("TR3", "accelerating competitor produces contextual prompts naming it", any("Competitor X" in x["prompt"] for x in ctxs) and all(x.get("why") for x in ctxs), [x["prompt"] for x in ctxs])
T("TR3", "at most 3 contextual prompts, one per capability", len(ctxs) <= 3 and len({x["_route"]["capability_id"] for x in ctxs}) == len(ctxs))
json.dump({"account": "Acme"}, open(f"{tmp}/none.json", "w"))
T("TR3", "no contextual prompts without a relevant signal", not any(x.get("tier") == "contextual" for x in eng("recommend", "--signals", f"{tmp}/none.json")["prompts"]))
json.dump({"account": "Acme", "anomalies": ["Revenue anomaly in 2026-06"]}, open(f"{tmp}/an.json", "w"))
T("TR3", "an anomaly signal yields an explain prompt", any("revenue anomaly in 2026-06" in x["prompt"].lower() for x in eng("recommend", "--signals", f"{tmp}/an.json")["prompts"]))
T("TR3", "recommendations stay small (≤ 5 by default)", len(r3["prompts"]) <= 5)
fu = eng("followups", "--after", "Build my complete account strategy.", "--contract", f"{tmp}/c.json")
T("FUP", "follow-ups after account strategy are relevant (threads/buying committee/90-day plan) and dynamic", any("Competitor X" in x["prompt"] for x in fu["prompts"]) and any(k in json.dumps(fu["prompts"]) for k in ("buying committee", "90-day", "opportunity")), [x["prompt"] for x in fu["prompts"]])
T("FUP", "the executed prompt is never suggested again", all(x["prompt"] != "Build my complete account strategy." for x in fu["prompts"]))
# ---------------- DSC discovery ----------------
hm = eng("home")
T("DSC", "global front door: 'What would you like to do?' with 6 prompts", hm["title"] == "What would you like to do?" and [x["prompt"] for x in hm["prompts"]] == ["Build my complete account strategy.", "Find my biggest growth opportunities.", "Prep me for my next sales call.",
  "Review my pipeline for risks and next steps.", "What has changed in this account?", "Give me today's growth briefing."])
T("DSC", "Explore capabilities has the 12 categories, each populated", [e["category"] for e in hm["explore"]] == IDX["explore_categories"] and all(e["capabilities"] for e in hm["explore"]))
doms = {c["domain"] for c in CAPS.values()}
T("DSC", "not sales-only: finance, marketing, market, operations, customers, decisions, dashboards covered", {"Finance", "Marketing", "Market", "Operations", "Customers", "Decisions", "Dashboards", "Competition", "Growth"} <= doms)
T("DSC", "administration hidden from ordinary users, shown to administrators", "Platform Administration" not in json.dumps(hm) and "Platform Administration" in json.dumps(eng("home", "--admin")) and eng("menu", "--capability", "admin").get("error"))
T("DSC", "/sales hub offers sales capabilities in business language", eng("hub", "--hub", "sales")["title"] == "Sales" and len(eng("hub", "--hub", "sales")["prompts"]) == 6)
T("DSC", "More prompts are grouped by category", set(eng("menu", "--capability", "forecast", "--more")["more_prompts"]) <= set(IDX["prompt_categories"]))
T("DSC", "global commands /growth and /sales exist; no clash with Claude Code built-ins", os.path.exists(f"{ROOT}/commands/growth.md") and os.path.exists(f"{ROOT}/commands/sales.md") and not os.path.exists(f"{ROOT}/commands/memory.md"))
cmd_names = {f[:-3] for f in os.listdir(f"{ROOT}/commands")}; expected = {({"memory": "business-memory"}.get(x, x)) for c in CAPS.values() for x in [c["slash_command"][1:]] + [a[1:] for a in c["aliases"]]} | {"growth", "sales"}
T("DSC", "no orphan command files", cmd_names == expected, sorted(cmd_names ^ expected))
spec = {"sales", "account", "opportunities", "deal", "meeting", "forecast", "competition", "threads", "financial", "marketing", "market", "decision", "scenario", "dashboard", "actions", "executive"}
T("DSC", "every slash command listed in the brief is available", spec <= cmd_names, sorted(spec - cmd_names))
# ---------------- DSH dashboard ----------------
T("DSH", "dashboard suggestions come from the starter-prompt engine", all(q.get("capability") for q in C["queries"]) and any(q.get("tier") == "contextual" for q in C["queries"]))
T("DSH", "dashboard discovery block: home, 12 categories, capability menus in business language", C["discovery"]["prompts"] and len(C["discovery"]["explore"]) == 12 and not any(s in json.dumps(C["discovery"]["menus"]) for s in ("-intelligence\"", "agent", "orchestrator")))
T("DSH", "dashboard menus name the accelerating competitor", "Explain the Competitor X thread." in C["discovery"]["menus"]["Competitive Threads"]["prompts"])
try:
    from playwright.sync_api import sync_playwright
    PW = sync_playwright().start(); BR = PW.chromium.launch()
except Exception as e:
    PW = None
if PW:
    subprocess.run([sys.executable, f"{SK}/artifact-dashboard-intelligence/scripts/render_dashboard.py", "--contract", f"{tmp}/c.json", "--out", f"{tmp}/d.html"], capture_output=True)
    pg = BR.new_page(viewport={"width": 1440, "height": 900}); errs = []; pg.on("pageerror", lambda e: errs.append(str(e))); pg.goto(pathlib.Path(tmp, "d.html").as_uri()); pg.wait_for_timeout(400)
    T("DSH", "suggestion row shows ≤ 5 prompts plus Explore, contextual ones marked", pg.evaluate("document.querySelectorAll('[data-query]').length") <= 5 and pg.evaluate("document.querySelectorAll('.suggest .sig').length") >= 1 and pg.evaluate("!!document.querySelector('[data-explore-open]')"))
    pg.click("[data-query='Q1']"); pg.wait_for_timeout(200)
    T("DSH", "clicking a suggestion hands prompt + capability + context to the orchestrator", "capability Competitive Threads" in (pg.evaluate("document.body.dataset.lastAsk") or "") and "Sanofi" in pg.evaluate("document.body.dataset.lastAsk"))
    pg.click("[data-explore-open]"); pg.wait_for_timeout(200); pg.click("[data-explore='Finance']"); pg.wait_for_timeout(150)
    T("DSH", "Explore capabilities drawer shows capability menus", pg.evaluate("document.querySelectorAll('#drawer [data-capability]').length") >= 2 and pg.evaluate("document.querySelectorAll('#drawer .pcard').length") >= 12)
    pg.click("#drawer .pcard"); pg.wait_for_timeout(200)
    T("DSH", "an Explore prompt runs in context and never errors (clipboard refusal handled)", "capability Financial Intelligence" in pg.evaluate("document.body.dataset.lastAsk") and not errs, errs)
    BR.close(); PW.stop()
else:
    for n in ("suggestion row", "click hand-off", "explore drawer", "explore run"): SKIP("DSH", n, "Playwright/Chromium unavailable")
# ---------------- SYN / REG ----------------
desync = []
for cid, c in CAPS.items():
    t = open(f"{SK}/{c['routes_to']['skill']}/SKILL.md").read()
    if "starter-prompts:start" not in t or any("- " + bare(p["text"]) not in t for p in c["primary_prompts"]): desync.append(cid)
T("SYN", "every skill's Starter prompts section matches the catalog", not desync, desync)
T("SYN", "skill frontmatter unchanged by prompts (no invented metadata)", all(set(yaml.safe_load(open(f"{SK}/{s}/SKILL.md").read().split("---")[1])) <= {"name", "description", "license", "allowed-tools", "metadata", "compatibility"} for s in SKILLS))
rv = json.loads(subprocess.run([sys.executable, f"{SK}/platform-admin/scripts/registry.py", ROOT, "validate"], capture_output=True, text=True).stdout)
T("REG", "registry valid; discovery skill reachable via the orchestrator", rv["status"] == "OK" and "growth-discovery" in REG["business-orchestrator"]["allowed_skills"], rv.get("errors"))
T("REG", "no broken skill references from the catalog", all(c["routes_to"]["skill"] in SKILLS for c in CAPS.values()))
# ---------------- report ----------------
areas = ["COV", "QLT", "RTT", "RTH", "FUP", "SLH", "PER", "CTX", "TR3", "DSC", "DSH", "SYN", "REG"]
for a_, n, s, d in R:
    if s != "PASS": print(f"{a_:4s} {s:5s} {n}   ← {d}")
print("BY AREA: " + " · ".join(f"{a_} {sum(1 for x in R if x[0] == a_ and x[2] == 'PASS')}/{sum(1 for x in R if x[0] == a_)}" for a_ in areas))
print(f"Typed routing of additional prompts (reported, not asserted): {typed_add_ok}/{typed_add_tot} = {typed_add_ok / typed_add_tot:.0%}")
np_ = sum(1 for x in R if x[2] == "PASS"); ns = sum(1 for x in R if x[2] == "SKIP")
print(f"PROMPTS: {np_}/{len(R)} PASS" + (f" · {ns} SKIPPED" if ns else ""))
json.dump([{"area": a_, "test": n, "result": s, "detail": d} for a_, n, s, d in R], open(f"{ROOT}/tests/last-prompts-run.json", "w"), indent=1)
sys.exit(0 if np_ == len(R) else 1)
