#!/usr/bin/env python3
"""
agent_planner.py: Intent Understanding + Agent Planner (control plane).

Turns a natural-language business request into an execution plan: intent, mode (ASK / PREPARE /
INVESTIGATE / WATCH / DECIDE / ACT), entities, decision altitude (role), and a DAG of steps. Each step
names its agent, skills, data sources, tools, reasoning tier (via model_router policy), dependencies,
parallel group, and approval requirement. Doing the minimum necessary work comes first:
  - memory reuse: if a fresh summary exists and the delta is not material → a short "reuse" plan
  - platform steps (context, memory, delta, validation, governance) are deterministic T0 wherever possible
  - T4 is never planned by default; it appears only as a conditional escalation

USAGE
  python agent_planner.py "Find $20M of potential opportunity in <account> over the next 12 months" \
      [--memory-db mem.db] [--delta delta.json] [--role ceo|cro|cfo|coo|manager|seller|investor] [--registry registry/agent-registry.json] [--out plan.json]
The plan is a proposal the Business Orchestrator follows and may revise (the LLM can refine the steps);
every revision is logged in the execution trace.
"""
import argparse, json, re, sqlite3, os
from datetime import datetime, timedelta

INTENTS = [  # (intent, mode, patterns): the first strong match wins; scores are summed
 # ---- V8: narrowly scoped patterns that must outrank the generic ones below
 ("scenario", "DECIDE", r"^what (happens )?if\b|impact of this scenario"),
 ("competitive_ground", "INVESTIGATE", r"\b(threat|thread)s?\b.*\b(evidence|counter-evidence|start|accelerat|next)|evidence behind (this|the) .*threat|about (this|the) .*threat|competitive (threads?|response)|record the outcome of this competitive"),
 ("deal_analysis", "INVESTIGATE", r"\b(this|the|my) deal\b|deal (strategy|review|momentum|health)|\bclose plan\b|prevent us from winning|decision process|missing stakeholders"),
 ("rfp", "PREPARE", r"\brfps?\b|evaluation criteria|compliance matrix|questionnaire|\bbid\b|contract terms|answers? from approved content|need an expert"),
 ("admin", "ASK", r"platform health|active capabilities|assistant performance|governance events|^show me (errors|usage)\.?$|recent traces|evaluation scores|regression tests|policy violations|tenant isolation|underperforming capability|approval turnaround|data-source freshness|cost by team|what a request cost"),
 ("meeting_followup", "ACT", r"\b(from|after) the meeting\b|call notes|commitments made|based on this meeting|log my meeting|across my meetings|follow-?up email|summarize the meeting"),
 ("challenge", "DECIDE", r"\bchallenge\b|what could change|what are you missing|downside|show (me )?(the )?evidence|\bwhy\?|alternative scenarios"),
 ("outcome_review", "ASK", r"what happened after|did (it|that) work|result of (our|the) (last )?(recommendation|action)"),
 ("learning_review", "ASK", r"what (did|have) we learn"),
 ("action", "ACT", r"\b(execute|update the crm|create (a |an )?(task|opportunity|meeting)|send|schedule|draft (the |an? )?(email|proposal)|trigger)\b|highest-priority actions|what should i do today|overdue actions|prioritize my actions|actions (linked|by owner|waiting|need approval|had the most)|completed actions|escalate this action|approval history|cancel an action|follow-up task"),
 # ---- V8: capability intents (lead agent discovered from the registry by the skill it serves)
 ("briefing", "ASK", r"(?<!executive )(?<!pre-meeting )\bbriefing\b(?!.*(account|meeting))|growth briefing|daily briefing|overnight|needs my attention today|today'?s (opportunities|risks)|priorities for today|catch me up|moved yesterday|close yesterday|\btoday\b.*\b(signals|due)\b|this week so far|prepare for tomorrow|before my meetings"),
 ("relationships", "ASK", r"stakeholder|relationship|champion|buying committee|engage next|introduce me|executive engagement|losing access|single-threaded|executive sponsorship|who has influence"),
 ("win_loss", "ASK", r"why we (won|lost)|win/?loss|loss (patterns?|reasons?)|lessons from (historical|past) deals|past outcomes|losing to|wins have in common|win rates? (by|against)|how we sell|statistically reliable"),
 ("signals", "ASK", r"growth signals|compound signals|emerging opportunities across|becoming (more attractive|risky)|why this signal|connect the dots|signals? (should sales|from three)|expansion signals|evidence chain|signals? (are )?weakening|margin-erosion|executive-access|route this signal"),
 ("knowledge", "ASK", r"\bknowledge\b|previous work|similar past work|similar situations|supporting evidence|authoritative|latest version|current policy|approved position|case studies|stale content|contradict each other|commit in the contract|pricing guidance|proposals for similar"),
 ("memory_recall", "ASK", r"what do we (already )?know|show me the history|what decisions have we made|previous outcomes|business memory|what did we predict|decisions still in force|assumptions did we record|past recommendations|forget an outdated|correct a fact|how sure we are|last updated"),
 ("twin", "ASK", r"digital twin|customer (state|twin|forecast)|target state|account 360|full picture|what-if scenario on this customer|historical trends|set a target|current state|state of the customer|(financial|competitive|relationship) state|every snapshot|likely next for this customer|why did this account change"),
 ("data_analysis", "INVESTIGATE", r"\bdataset\b|this data\b|this file\b|patterns? do you see|data (quality|reliable)|\bour data\b|duplicates|reconcile|clean up our crm|missing or stale|two datasets"),
 ("research", "INVESTIGATE", r"research .*(prospect|for me)|why this account, why now|reach out|outreach|target accounts|\bprospects?\b|linkedin message|customer stories fit|point of view|contact first|no reply|draft outreach"),
 ("market_view", "ASK", r"\bmarkets?\b|\bindustry\b|market trends|benchmarks?|regulatory changes"),
 ("executive_view", "ASK", r"state of the business|changed materially|leadership focus|biggest (opportunities|risks)\.|(?<!pre-meeting )executive briefing\.?$|should concern me|executive intervention|growth (accelerating|weakening)|strategic signals|against plan|board update|investor view|kpis moved|forecast last time"),
 ("watch", "WATCH", r"\b(alert me|watch(es)?|monitor|notify me|tell me if)\b"),
 ("cross_functional", "INVESTIGATE", r"why is .* (behind|down|up)|what(?:'s| is) driving|root cause|analyze my business|what should i know today|unusual patterns|most important signals|needs attention|behind plan|drop in retention|margin fall|gap to plan|explain this number|drivers matter|compare segments|what happened, and why|revenue variance|likely to happen next|operations slowing|changed in the business"),
 ("meeting_prep", "PREPARE", r"\bprep(are)?( me)?\b.*\bmeeting\b|\bmeeting (prep|brief)|brief me|sales call|next call|before (this|my|the) meeting|meeting strategy|questions (should )?i (should )?ask|avoid discussing|likely objections|who will attend|5-minute briefing|pre-meeting|agenda for the meeting|commitments do we owe|risks should i raise|customer'?s priorities|cio meeting"),
 ("meeting_followup", "ACT", r"transcript|follow[- ]?up|process (my|the) (call|meeting)|after (my|the) meeting"),
 ("dashboard", "PREPARE", r"\bdashboard\b|command cent(er|re)|executive view|cockpit|growth command center|dashboard i need"),
 ("account_strategy", "PREPARE", r"(complete|full|integrated)?\s*(account|growth) (strategy|plan)\b|build (a |the )?(complete )?(account|growth) strategy"),
 ("marketing_view", "ASK", r"what is marketing telling|marketing (signals|engagement|telling|intelligence)|campaign (influence|impact)|marketing activity|buying intent|engagement trends|campaigns|warming|cooling|marketing-to-revenue|abm|marketing signals|intent surges|marketing creating|marketing timeline|engaging with our marketing|competitor-related content"),
 ("financial_story", "ASK", r"financial (story|position|health|signals|picture)|\bfinancials?\b|ebitda|free cash flow|\bmargins?\b trend|five years of financials|financial changes matter|profitability trends|financial signals|revenue growth\.|cash-flow|company investing|financial pressure|business-unit performance|prior years|capex|financial figures"),
 ("competitive_ground", "INVESTIGATE", r"competitors? (gaining|winning|taking) (ground|share)|where are competitors|competitive (threads?|momentum)"),
 ("account_change", "ASK", r"what'?s changing|what is changing"),
 ("opportunity_discovery", "INVESTIGATE", r"\b(find|discover|identify|show)\b.*\b(opportunit|growth|whitespace|expan)|whitespace|\$\s?\d+\s?[mbk]\b.*(opportunit|growth)|prioritize my opportunities|opportunities matter|where should i focus first|cross-sell|upsell|focus on this quarter|account plays"),
 ("pricing", "INVESTIGATE", r"\b(discount|pricing|price|quote|margin on)\b|commercial (structure|scenario)|discount|price sensitivity|guardrails|expected value by discount"),
 ("scenario", "DECIDE", r"what (happens )?if|\bscenario|what-if|model a|best, base|impact of (losing|winning)|strategic scenarios|reps do we need|assumptions matter|gap to target|capacity plan|stress-test|close the gap"),
 ("decision", "DECIDE", r"\bshould (we|i)\b|\bdecide\b|\boptions\b|trade-?off|recommend(ation)? on|evaluate this decision|evidence supports each option|risks of each option|decision brief|this decision|record this decision|decisions need my attention"),
 ("competitive", "INVESTIGATE", r"\bcompetit|competitive landscape|competitive threats|displacement|battlecard|exposed to competitors|competitive signals|competitive patterns"),
 ("customer_health", "INVESTIGATE", r"\b(churn|renewal|adoption|health|retention)\b|expansion-ready|ready to expand|customer growth|whitespace in our customer|existing customers|expansion potential|products should we expand|customer success|customers need attention|health across|save this renewal"),
 ("deal_analysis", "INVESTIGATE", r"\b(deal|opportunity)\b.*\b(risk|win|close|stuck|slip)|\bO\d{3}\b|why is (this|the) deal"),
 ("pipeline_forecast", "ASK", r"\b(forecast|pipeline|quarter|hit the number|coverage)\b|stalled|slip|intervention|pipeline by"),
 ("market_event", "INVESTIGATE", r"\b(regulat|announce|acquisition|m&a|market (event|change)|tariff|macro)"),
 ("solution", "PREPARE", r"\b(solution|architecture|proposal|rfp|transformation program)\b|target architecture|requirements to|integration (requirements|dependencies)|technical risks|solution overview|implementation roadmap|delivery model|value case|reference solutions|architecture view|design the target"),
 ("data_quality", "INVESTIGATE", r"\b(data quality|duplicates|reconcile|stale data|is (our|the) data)\b"),
 ("delta", "ASK", r"what changed|since (last|our last)"),
 ("business_health", "ASK", r"how is (the|my|our) business|business (performing|health)|how are we doing|what is happening in my business"),
 ("account_intelligence", "ASK", r"account (360|strategy|plan|intelligence)|tell me about|what is happening (with|at|in)|what'?s happening with|briefing on (this|the) account|account briefing"),
]
ROLE = {"seller": "What should I do today", "manager": "Where is my team at risk", "cro": "How is revenue performing", "cfo": "Revenue, margin and cash",
        "coo": "Operational constraints", "ceo": "Business performance and decisions that matter", "investor": "Growth, efficiency, quality and risk"}
TIERCOST = {"T0": 0, "T1": 1, "T2": 4, "T3": 12, "T4": 20}  # relative cost per 1k tokens
TOK = {"T0": 0, "T1": 2.5, "T2": 2.5, "T3": 3.6, "T4": 5.0}  # expected k tokens per agent step (packet + reply)

CAP_INTENT_SKILL = {"briefing": "daily-growth-briefing", "relationships": "relationship-intelligence", "win_loss": "win-loss-intelligence", "signals": "growth-signal-orchestrator",
                    "knowledge": "knowledge-intelligence", "memory_recall": "business-memory", "twin": "customer-digital-twin", "data_analysis": "data-intelligence", "rfp": "rfp-response-composer",
                    "research": "account-intel-outreach", "admin": "platform-admin", "market_view": "market-intelligence", "executive_view": "executive-command-center"}

def S(step, agent, skills, data, tier, deps=(), group=None, approval=False, why="", tools=None, conditional=None):
    return {"step": step, "agent": agent, "skills": skills, "data": data, "tools": tools or ([] if tier == "T0" else ["Agent tool → " + agent]),
            "tier": tier, "depends_on": list(deps), "parallel_group": group, "approval_required": approval, "why": why, **({"conditional": conditional} if conditional else {})}

def find_registry(explicit):
    if explicit: return explicit
    d = os.path.dirname(os.path.abspath(__file__))
    for _ in range(5):
        if os.path.isdir(os.path.join(d, "registry", "manifests")): return os.path.join(d, "registry", "manifests")
        d = os.path.dirname(d)
    return None
def load_registry(path):
    R = {}
    if not path: return R
    import glob, yaml
    for f in glob.glob(os.path.join(path, "*.yaml")):
        if os.path.basename(f).startswith("_"): continue
        m = yaml.safe_load(open(f)); R[m["agent_id"]] = m
    return R

ap = argparse.ArgumentParser()
ap.add_argument("request"); ap.add_argument("--memory-db"); ap.add_argument("--delta"); ap.add_argument("--role"); ap.add_argument("--registry"); ap.add_argument("--out")
ap.add_argument("--freshness-days", type=int, default=7); ap.add_argument("--manifests"); ap.add_argument("--capability")
a = ap.parse_args()
r = a.request.strip(); rl = r.lower()

# ---- intent: score all patterns; primary = best; secondary = the others that matched
hits = [(i, m) for i, m, p in INTENTS if re.search(p, rl)]
intent, mode = hits[0] if hits else ("account_intelligence" if re.search(r"\b[A-Z][a-z]+\b", r) else "business_health", "ASK")
if a.capability:   # V8: a starter prompt or slash command already knows its capability; route deterministically
    import glob as _g, yaml as _y
    _d = os.path.dirname(os.path.abspath(__file__)); _cat = None
    for _ in range(5):
        _c = os.path.join(_d, "skills", "growth-discovery", "references", "starter-prompts", a.capability + ".yaml")
        if os.path.exists(_c): _cat = _c; break
        _d = os.path.dirname(_d)
    if not _cat: print(json.dumps({"error": f"unknown capability '{a.capability}'"})); sys.exit(2)
    intent = _y.safe_load(open(_cat))["capability"]["routes_to"]["intent"]
    mode = next((m for i, m, p in INTENTS if i == intent), "ASK"); hits = [(intent, mode)] + [h for h in hits if h[0] != intent]
secondary = [h[0] for h in hits[1:4]]

# ---- entities
amt = re.search(r"\$\s?(\d+(?:\.\d+)?)\s?([mbk])", rl)
value_target = float(amt.group(1)) * {"m": 1e6, "b": 1e9, "k": 1e3}[amt.group(2)] if amt else None
horizon = re.search(r"(\d+)\s*(months?|quarters?|weeks?|years?)", rl)
ids = re.findall(r"\b[AO]\d{3}\b", r)
known, entity, entity_known = [], None, False
if a.memory_db and os.path.exists(a.memory_db):
    con = sqlite3.connect(a.memory_db)
    known = [(row[0], row[1]) for row in con.execute("SELECT id,label FROM nodes WHERE type IN ('account','opportunity')")]
    for nid, label in known:
        if nid in ids or (label and len(label) > 3 and label.lower() in rl):
            entity, entity_known = nid, True; break
if not entity:
    stop = {"Find", "What", "Why", "How", "Show", "Prepare", "Create", "Draft", "Update", "Tell", "Challenge", "The", "My", "Our", "I", "Execute", "Is", "Should", "Alert"}
    caps = [w for w in re.findall(r"\b[A-Z][A-Za-z&]+(?:\s[A-Z][A-Za-z&]+)?\b", r) if w.split()[0] not in stop and not re.match(r"^(CRM|CEO|CFO|CRO|COO|AI)$", w)]
    entity = ids[0] if ids else (caps[0] if caps else None)
role = a.role or ("ceo" if intent == "business_health" else None)

# ---- memory reuse check
reuse, last = False, None
if a.memory_db and entity_known:
    row = sqlite3.connect(a.memory_db).execute("SELECT at, run_id FROM summaries WHERE entity=? ORDER BY at DESC LIMIT 1", (entity,)).fetchone()
    if row:
        last = {"run": row[1], "at": row[0]}
        material = True
        if a.delta and os.path.exists(a.delta):
            d = json.load(open(a.delta)); material = d.get("materiality", {}).get("material_changes", 1) > 0
        fresh = datetime.fromisoformat(row[0]) > datetime.now() - timedelta(days=a.freshness_days)
        reuse = fresh and not material and intent in ("account_intelligence", "delta", "business_health", "pipeline_forecast")

# ---- platform prefix (T0, deterministic)
P = [S("context", "business-orchestrator", ["business-context-discovery"], ["business_context_profile"], "T0", why="load the profile (reuse unless contradicted)", tools=["memory_graph.py profile-get"]),
     S("memory", "business-orchestrator", ["business-memory"], ["memory_graph"], "T0", ["context"], why="L1–L3 recall for the entity", tools=["memory_graph.py recall"]),
     S("delta", "business-orchestrator", ["business-memory", "data-intelligence"], ["sources"], "T0", ["memory"], why="what changed since last time — answer this first", tools=["delta_engine.py", "memory_graph.py delta"])]
if reuse:
    plan = P + [S("answer_from_memory", "business-orchestrator", ["business-memory"], ["memory_graph"], "T2", ["delta"], why="no material change since " + last["at"][:10] + ": reuse the previous conclusion; report only the delta")]
else:
    new_entity = bool(entity) and not entity_known and intent in ("dashboard", "opportunity_discovery", "account_intelligence", "meeting_prep", "solution", "account_strategy", "financial_story", "competitive_ground")
    B = []
    if new_entity:
        B.append(S("research_entity", "research-agent", ["knowledge-intelligence"], ["web", "document_repositories"], "T1", ["delta"], "g1", why=f"'{entity}' not in memory: acquire sourced evidence (priorities, financials, initiatives, technology, leadership)"))
    if intent in ("opportunity_discovery",):
        B += [S("account_baseline", "account-intelligence-agent", ["customer-digital-twin", "account-intelligence-swot-planning"], ["crm", "erp_read", "product_usage"], "T2", ["delta"], "g1", why="existing relationship, footprint, 360"),
              S("relationships", "relationship-agent", ["relationship-intelligence"], ["crm", "email_calendar_meta"], "T2", ["delta"], "g1", why="stakeholder map, buyer access"),
              S("market_signals", "market-intelligence-agent", ["market-intelligence"], ["web"], "T2", ["research_entity"] if new_entity else ["delta"], "g2", why="industry and strategic events → implications"),
              S("competition", "competitive-intelligence-agent", ["competitive-intelligence"], ["crm", "web"], "T2", ["research_entity"] if new_entity else ["delta"], "g2", why="competitive presence and displacement"),
              S("hypotheses", "opportunity-agent", ["growth-opportunity-discovery"], ["install_base"], "T3" if (value_target or 0) >= 1e6 else "T2",
                ["account_baseline", "relationships", "market_signals", "competition"], why=f"generate and size opportunity hypotheses{' toward $' + format(value_target / 1e6, 'g') + 'M' if value_target else ''}"),
              S("solutions", "solution-architect-agent", ["solution-architecture"], ["document_repositories"], "T3", ["hypotheses"], "g3", why="problem → capability → solution → value for the top hypotheses"),
              S("pricing_view", "pricing-commercial-agent", ["pricing-intelligence"], ["pricing_history", "benchmarks"], "T3", ["hypotheses"], "g3", why="commercial model and price bands where evidence exists", conditional="only if pricing evidence exists")]
    elif intent in CAP_INTENT_SKILL:
        sk = CAP_INTENT_SKILL[intent]; REG0 = load_registry(find_registry(a.manifests))
        lead = next((m["agent_id"] for m in REG0.values() if m.get("runtime") == "subagent" and m.get("status") in ("ACTIVE", "EXPERIMENTAL") and sk in (m.get("preload_skills") or [])), None) or \
               next((m["agent_id"] for m in REG0.values() if m.get("runtime") == "subagent" and m.get("status") in ("ACTIVE", "EXPERIMENTAL") and sk in m.get("allowed_skills", [])), None)
        B += [S("capability", lead or "business-orchestrator", [sk], ["memory_graph", "crm"], "T2" if lead else "T0", ["delta"], why=f"{sk} (lead agent discovered from the registry)")]
    elif intent == "dashboard":
        B += [S("dashboard_design", "dashboard-intelligence-agent", ["dashboard-intelligence"], ["memory_graph", "business_context_profile"], "T2", ["delta"], why="persona, entity, objective, domains, KPI emphasis → dashboard spec"),
              S("correlate", "business-orchestrator", ["growth-signal-orchestrator"], ["domain outputs"], "T0", ["delta"], why="cross-domain patterns for insights", tools=["cross_domain_correlator.py"]),
              S("dashboard_contract", "business-orchestrator", ["dashboard-intelligence"], ["memory_graph", "crm"], "T0", ["correlate", "dashboard_design"], why="provider → bundle → validated Dashboard Contract (every number in code)", tools=["demo_provider.py | production_provider.py", "dashboard_builder.py --validate"]),
              S("contract_review", "dashboard-intelligence-agent", ["dashboard-intelligence"], ["contract"], "T2", ["dashboard_contract"], why="evidence and persona-fit review; optional narrative rephrase keeping evidence ids"),
              S("render_artifact", "business-orchestrator", ["artifact-dashboard-intelligence"], ["contract"], "T0", ["contract_review"], why="render and publish the Enterprise Growth Command Center", tools=["render_dashboard.py", "Artifact publish"])]
    elif intent == "account_strategy":
        B += [S("account_baseline", "account-intelligence-agent", ["customer-digital-twin", "account-intelligence-swot-planning"], ["crm", "erp_read", "product_usage"], "T2", ["research_entity"] if new_entity else ["delta"], "gA", why="360, footprint, twin"),
              S("relationships", "relationship-agent", ["relationship-intelligence"], ["crm", "email_calendar_meta"], "T2", ["delta"], "gA", why="relationship map"),
              S("market_signals", "market-intelligence-agent", ["market-intelligence"], ["web"], "T2", ["research_entity"] if new_entity else ["delta"], "gA", why="market and strategic events"),
              S("correlate", "business-orchestrator", ["growth-signal-orchestrator"], ["domain outputs"], "T0", ["account_baseline", "relationships", "market_signals"], why="cross-domain patterns P1–P5", tools=["cross_domain_correlator.py"]),
              S("hypotheses", "opportunity-agent", ["growth-opportunity-discovery"], ["install_base"], "T3", ["correlate"], why="cross-domain opportunities", tools=["opportunity_builder.py", "Agent tool → opportunity-agent"]),
              S("twin_snapshot", "business-orchestrator", ["customer-digital-twin"], ["memory_graph"], "T0", ["hypotheses"], why="snapshot all state domains", tools=["twin_state.py snapshot"]),
              S("plan_assembly", "account-intelligence-agent", ["account-intelligence-swot-planning"], ["domain outputs"], "T3", ["twin_snapshot"], why="12-section account plan with evidence", tools=["account_plan_builder.py", "Agent tool → account-intelligence-agent"])]
    elif intent in ("marketing_view", "financial_story", "competitive_ground", "account_change"):
        B += [S("correlate", "business-orchestrator", ["growth-signal-orchestrator"], ["domain outputs"], "T0", ["delta"], why="connect this domain to the others", tools=["cross_domain_correlator.py"])] if intent != "account_change" else \
             [S("twin_changes", "business-orchestrator", ["customer-digital-twin"], ["memory_graph"], "T0", ["delta"], why="what changed since the previous snapshot, by domain", tools=["twin_state.py changes", "domain_delta.py"])]
    elif intent in ("account_intelligence", "delta"):
        B += [S("account_view", "account-intelligence-agent", ["customer-digital-twin", "account-intelligence-swot-planning"], ["crm", "erp_read", "itsm_read", "product_usage"], "T2", ["delta"], why="360 and what changed")]
    elif intent == "meeting_prep":
        B += [S("prep", "meeting-intelligence-agent", ["meeting-intelligence-brief"], ["calendar", "crm", "itsm_read"], "T2", ["delta"], why="brief: landmines, commitments, questions"),
              S("stakeholders", "relationship-agent", ["relationship-intelligence"], ["crm", "email_calendar_meta"], "T2", ["delta"], "g1", why="who is in the room")]
    elif intent == "meeting_followup":
        B += [S("followup", "meeting-intelligence-agent", ["meeting-follow-through"], ["transcripts", "crm"], "T2", ["delta"], why="commitments, signals, CRM change set")]
    elif intent == "deal_analysis":
        B += [S("deal_review", "deal-strategy-agent", ["deal-intelligence"], ["crm", "transcripts"], "T2", ["delta"], why="health, risk drivers, close plan"),
              S("deal_relationships", "relationship-agent", ["relationship-intelligence"], ["crm"], "T2", ["delta"], "g1", why="committee gaps")]
    elif intent == "pipeline_forecast":
        B += [S("forecast", "pipeline-forecast-agent", ["pipeline-forecast-intelligence"], ["crm", "forecast_submissions"], "T2", ["delta"], why="P10/P50/P90, slippage, coverage")]
    elif intent == "pricing":
        B += [S("pricing", "pricing-commercial-agent", ["pricing-intelligence"], ["cpq_read", "pricing_history"], "T3", ["delta"], why="EV by discount, robustness, decisions in force")]
    elif intent == "competitive":
        B += [S("competitive", "competitive-intelligence-agent", ["competitive-intelligence"], ["crm", "web"], "T2", ["delta"], why="presence, early warning, threats")]
    elif intent == "customer_health":
        B += [S("health", "customer-growth-agent", ["renewal-expansion-radar", "growth-signal-orchestrator"], ["product_usage", "itsm_read", "crm"], "T2", ["delta"], why="adoption → health → risk → renewal → expansion")]
    elif intent == "market_event":
        B += [S("research_event", "research-agent", ["knowledge-intelligence"], ["web"], "T1", ["delta"], why="sourced facts about the event"),
              S("implications", "market-intelligence-agent", ["market-intelligence"], ["web"], "T2", ["research_event"], why="business implications"),
              S("exposure", "customer-growth-agent", ["growth-signal-orchestrator"], ["memory_graph"], "T2", ["implications"], why="which accounts and deals are exposed")]
    elif intent in ("scenario",):
        B += [S("scenario", "executive-decision-agent", ["scenario-planner"], ["analysis outputs"], "T3", ["delta"], why="driver scenarios and sensitivity")]
    elif intent in ("decision", "challenge"):
        B += [S("analysis", "executive-decision-agent", ["decision-intelligence", "business-intelligence-copilot"], ["analysis outputs"], "T3", ["delta"],
                why="options, evidence, trade-offs" + (" — challenge mode: steelman the alternative, list what would change the recommendation" if intent == "challenge" else ""))]
    elif intent == "solution":
        B += [S("solution", "solution-architect-agent", ["solution-architecture", "rfp-response-composer"], ["document_repositories"], "T3", ["delta"], why="solution design from approved capabilities")]
    elif intent == "data_quality":
        B += [S("data_check", "data-intelligence-agent", ["data-intelligence"], ["all authorized sources"], "T1", ["delta"], why="profile, duplicates, conflicts, freshness")]
    elif intent == "watch":
        B += [S("watch_define", "business-orchestrator", ["business-watch"], ["memory_graph"], "T0", ["delta"], approval=True, why="define watch; saving it needs confirmation")]
    elif intent in ("outcome_review", "learning_review"):
        B += [S("outcomes", "outcome-learning-agent", ["business-memory", "win-loss-intelligence"], ["memory_graph"], "T2", ["delta"], why="prediction → action → outcome → error → learning status")]
    elif intent == "action":
        B += [S("action_spec", "action-workflow-agent", ["action-center"], ["action_catalog"], "T1", ["delta"], why="precise action specification from the approved recommendation")]
    elif intent in ("business_health", "cross_functional"):
        B += [S("kpis", "business-orchestrator", ["executive-command-center"], ["all authorized"], "T0", ["delta"], why="adaptive KPIs for the role", tools=["kpi_engine.py"]),
              S("drivers", "executive-decision-agent", ["business-intelligence-copilot"], ["analysis outputs"], "T2", ["kpis"], why="what changed and why (driver tree)"),
              S("signals", "customer-growth-agent", ["growth-signal-orchestrator"], ["memory_graph"], "T2", ["delta"], "g1", why="cross-functional patterns")]
    # DYNAMIC DISCOVERY (V7.1): any ACTIVE/EXPERIMENTAL agent whose manifest lists this intent in `serves_intents`
    # joins the plan, so new or customer-specific agents are used without changing the planner.
    REG = load_registry(find_registry(a.manifests))
    planned = {s["agent"] for s in B}
    dyn = []
    for aid, m in sorted(REG.items()):
        if intent in (m.get("serves_intents") or []) and aid not in planned and m.get("status") in ("ACTIVE", "EXPERIMENTAL") and m.get("runtime") == "subagent":
            dyn.append(S(f"domain:{aid}", aid, m["allowed_skills"][:1], [d for d in m["allowed_data_sources"] if d not in ("memory_graph", "business_context_profile")][:3],
                         m["model_routing_policy"].get("default_tier", "T2"), ["research_entity"] if new_entity and any(s["step"] == "research_entity" for s in B) else ["delta"], "gD",
                         why=f"discovered in registry (serves '{intent}'): {m['description'][:90]}"))
    if dyn:
        B = [s for s in B if s["step"] not in ("correlate",)] + dyn + [s for s in B if s["step"] == "correlate"]
        for s in B:
            if s["step"] in ("hypotheses", "correlate", "plan_assembly", "dashboard_contract"):
                s["depends_on"] = sorted(set(s["depends_on"]) | {d["step"] for d in dyn})
    disabled = [s["agent"] for s in B if s["agent"] in REG and REG[s["agent"]].get("status") in ("DISABLED", "DEPRECATED")]
    B = [s for s in B if s["agent"] not in disabled]
    # data validation before high-impact analysis
    if intent in ("opportunity_discovery", "pricing", "decision", "pipeline_forecast", "business_health", "scenario", "account_strategy", "financial_story") and not new_entity:
        B.insert(0, S("validate_data", "data-intelligence-agent", ["data-intelligence"], ["sources"], "T1", ["delta"], "g0", why="freshness, conflicts, duplicates before high-impact analysis"))
    # Compose secondary intents: a request can need several domain agents ("should we discount O010?" = decision + pricing).
    CORE = {"pricing": ("pricing", "pricing-commercial-agent", ["pricing-intelligence"], ["cpq_read", "pricing_history"], "T3"),
            "competitive": ("competitive", "competitive-intelligence-agent", ["competitive-intelligence"], ["crm", "web"], "T2"),
            "customer_health": ("health", "customer-growth-agent", ["renewal-expansion-radar"], ["product_usage", "itsm_read"], "T2"),
            "deal_analysis": ("deal_review", "deal-strategy-agent", ["deal-intelligence"], ["crm"], "T2"),
            "pipeline_forecast": ("forecast", "pipeline-forecast-agent", ["pipeline-forecast-intelligence"], ["crm"], "T2"),
            "market_event": ("implications", "market-intelligence-agent", ["market-intelligence"], ["web"], "T2")}
    have = {s["agent"] for s in B}
    for si in secondary[:2]:
        if si in CORE and CORE[si][1] not in have:
            st, ag, sk, da, ti = CORE[si]
            B.insert(0, S(st, ag, sk, da, ti, ["delta"], "g0", why=f"secondary intent '{si}' composed into the plan")); have.add(ag)
    last_steps = [s["step"] for s in B if not any(s["step"] in x["depends_on"] for x in B)] or ["delta"]
    tail = [S("evidence_validation", "business-orchestrator", [], ["agent results"], "T0", last_steps, why="contract, provenance, conflicts, injection scan", tools=["evidence_validator.py"])]
    high = intent in ("opportunity_discovery", "pricing", "decision", "challenge", "action", "scenario", "account_strategy") or (value_target or 0) >= 1e6
    if high:
        tail.append(S("governance_review", "governance-risk-agent", ["platform-admin"], ["policy", "registry"], "T2", ["evidence_validation"], why="evidence sufficiency, permissions, sensitivity, hallucination risk"))
    if intent in ("opportunity_discovery", "decision", "challenge", "scenario", "pricing", "account_strategy"):
        tail.append(S("decision_framing", "executive-decision-agent", ["decision-intelligence"], ["validated results"], "T3", [tail[-1]["step"]], why="options, trade-offs, owner, deadline, approval"))
    if intent in ("opportunity_discovery", "meeting_followup", "deal_analysis", "customer_health", "action", "decision", "pricing", "account_strategy"):
        tail.append(S("action_prep", "action-workflow-agent", ["action-center"], ["action_catalog"], "T1", [tail[-1]["step"]], why="turn recommendations into catalog actions"))
        tail.append(S("policy_gate", "business-orchestrator", ["action-center"], ["policy"], "T0", ["action_prep"], approval=True, why="risk, policy, autonomy, approval → human approval where required", tools=["policy_gate.py"]))
    tail.append(S("memory_update", "business-orchestrator", ["business-memory"], ["memory_graph"], "T0", [tail[-1]["step"]], why="facts, hypotheses, decisions, actions, summary, trace", tools=["memory_graph.py", "trace.py"]))
    tail.append(S("escalation_T4", "growth-expert", ["business-memory"], ["packet"], "T4", ["decision_framing"] if any(t["step"] == "decision_framing" for t in tail) else ["evidence_validation"],
                  why="independent challenge review", conditional="only if T3 confidence < 0.6, evidence conflicts materially, or impact ≥ $5M"))
    plan = P + B + tail
    # Stable topological order: a step is listed only after every step it depends on (authored order kept otherwise).
    names = {s["step"] for s in plan}; done, ordered, rest_ = set(), [], list(plan)
    while rest_:
        ready = [s for s in rest_ if all(d in done or d not in names for d in s["depends_on"])]
        if not ready: raise SystemExit(json.dumps({"error": "dependency cycle in plan", "steps": [s["step"] for s in rest_]}))
        s = ready[0]; ordered.append(s); done.add(s["step"]); rest_.remove(s)
    plan = ordered

for s in plan:
    s["est_ktokens"] = 0.6 if s["step"] == "answer_from_memory" else (4.5 if s["step"].startswith("research") else TOK[s["tier"]])
cost = round(sum(TIERCOST[s["tier"]] * s["est_ktokens"] for s in plan if not s.get("conditional")), 1)
groups = {}
for s in plan:
    if s["parallel_group"]: groups.setdefault(s["parallel_group"], []).append(s["step"])
agents = sorted({s["agent"] for s in plan if not s.get("conditional")})
out = {"dynamic_agents": [s["agent"] for s in plan if s["step"].startswith("domain:")] if not reuse else [], "request": r, "intent": intent, "secondary_intents": secondary, "mode": mode, "entity": entity, "entity_in_memory": entity_known,
       "value_target": value_target, "horizon": horizon.group(0) if horizon else None, "role": role, "altitude": ROLE.get(role),
       "memory_reuse": reuse, "last_analysis": last, "agents": agents, "steps": plan, "parallel_groups": groups,
       "approval_points": [s["step"] for s in plan if s["approval_required"]], "max_planned_tier": max((s["tier"] for s in plan if not s.get("conditional")), key=lambda t: TIERCOST[t]),
       "estimated_relative_cost": cost, "note": "Plan is a proposal; the orchestrator may refine it and logs every revision in the trace."}
print(json.dumps(out, indent=1))
if a.out: json.dump(out, open(a.out, "w"), indent=1)
