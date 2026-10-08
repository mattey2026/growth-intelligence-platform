# Changelog

## 8.0.0: Starter Prompts & Discovery (release candidate)
**Added**
- **growth-discovery skill:**
  - starter-prompt catalog: 34 capabilities, 204 primary and 342 additional prompts, outcomes, follow-ups, persona variants;
  - 13 personas, 7 prompt categories, 12 Explore categories;
  - `prompt_engine.py`: home, menu, hub, explore, recommend, follow-ups, resolve and route.
- **38 slash commands** (`commands/`, Claude Code native), including `/growth` and `/sales`. `/memory` is renamed `/business-memory` to avoid Claude Code's built-in command.
- **Orchestrator:** 13 capability intents (registry-discovered lead agents), priority patterns, and the `--capability` hint. Typed routing of primary prompts rose from **103/204 to 204/204**.
- **Dashboard:** context-aware suggestions from the engine (signal prompts marked), an Explore capabilities drawer, and the capability carried to the orchestrator.
- **Generated "Starter prompts" sections** in 32 SKILL.md files.
- **Tests and evals:** `tests/run_prompts.py` (263 tests) and live eval `discovery`.

**Fixed during the V8 build**
- *Routing:*
  - Half the platform's capabilities were unreachable by typed requests (no intents, or a fall-through to account intelligence).
  - Duplicate or ambiguous prompts across capabilities.
- *Generators:*
  - Invalid YAML in all 38 command files (unquoted colons; Claude Code's validator does not check command files).
  - A template spacing bug ("Watchthis account").
- *Engine and UI:*
  - `/sales` hub crash (argument order).
  - Unhandled clipboard refusal in the dashboard (it claimed a copy that had failed).
  - Contextual prompts crowding out the persona's own prompts.
  - Generic thread prompts when the competitor was known.

## 7.2.0: Dashboard Intelligence (release candidate)
**Added**
- **Skills:** dashboard-intelligence (design system, personas, metric definitions, providers, builder, state store) and artifact-dashboard-intelligence (Command Center renderer).
- **Agent:** dashboard-intelligence-agent (T2; read-only; no shell). It designs the experience and reviews the contract; T0 steps run in the orchestrator.
- **Contract:** `schemas/dashboard.schema.json`, with 18 object types including the 13-object dashboard model.
- **Providers:** demo (runs the real V7.1 engines on labelled demo inputs) and production (Business Memory plus CRM and billing exports; lists its data gaps).
- **Routing:** `dashboard` intent in the planner; five domain agents serve it through registry discovery.
- **Engine addition:** `marketing_signals.py` now also emits `normalized_signals` (backward compatible).
- **Tests and evals:** `tests/run_dashboard.py` (83 tests, headless Chromium) and live eval `dashboard-agent`.

**Fixed during the V7.2 build**
- *Trust:*
  - Anomaly rule mislabelled normal growth (now trend-adjusted).
  - Inconsistent revenue across widgets (snapshots now derived from the same series).
  - False zeros in production (exposure, growth drivers and new-opportunity value now "Not available").
- *Layout and readability:*
  - Grid spans ignored (CSS custom property).
  - 339px overflow in Marketing.
  - Unreadable margin bridge.
  - KPI truncation at 1280px.
  - Radar label collisions.
  - Timeline label clipping.
- *Correctness:*
  - Heatmap and timeline empty without a memory path.
  - Nested widget output printed as text.
  - Momentum colouring wrong for opportunity threads.
  - Stale thread titles.
  - Ask routing sent "renewal" questions to What changed.
- *Governance and access:*
  - Provenance marks clipped in long source cells.
  - State store not bound to its tenant.
  - Agent manifest given shell access (rejected by the registry; removed).

## 7.1.0: Enterprise Growth & Decision Intelligence (release candidate)
**Added**
- **Skills:** marketing-intelligence, financial-intelligence, competitive-thread-intelligence.
- **Agents:** marketing-intelligence-agent, financial-intelligence-agent, competitive-thread-agent.
- **Engines:**
  - `marketing_signals.py`, `financial_intel.py`, `competitive_threads.py` (persistent CompetitiveThread);
  - `cross_domain_correlator.py` (patterns P1–P5), `domain_delta.py`, `opportunity_builder.py`, `account_plan_builder.py`.
- **Memory:** typed domain objects (MarketingSignal, FinancialSignal, FinancialMetric, CompetitiveEvent, CompetitiveThread, CompetitiveHypothesis, CompetitiveOutcome, CampaignInfluence, AccountEngagement, CrossDomainPattern).
- **Digital twin:** eight state domains, snapshots, and "what changed since the previous snapshot".
- **Evidence:** `evidence_validator.py claims` enforces the six-type evidence contract.
- **Tracing:** V7.1 trace events and `trace.py check`.
- **Registry:** `serves_intents` drives dynamic discovery; the new `registry/skill-registry.json`.
- **Business model:** a B2B2C KPI framework (sell-in, sell-through, partner concentration, partner margin).
- **Policy:** marketing_data, financial_data and public_filings sources, the financial_confidential clearance, and a marketing role.
- **Tests and evals:** 104 V7.1 tests (tests/run_v71.py) and 4 live eval cases.

**Fixed during V7.1 testing**
- Marketing window helper type error.
- Thread serialization of structured fields.
- Asymmetric thread-family matching (split one competitor story into two threads).
- CompetitiveEvent without confidence.
- Trace order check too strict.
- Account-plan evidence not structured.
- Thread momentum and confidence counted counter-evidence as support.
- Opportunity threads treated competitor weakness as counter-evidence.
- Conflicts mode rejected list inputs.
- Planner listed steps before their dependencies (now topologically ordered).

**Unchanged:** all V7 skills and agents remain discoverable; the V7 suite passes 38/38.

## 7.0.0-beta.1: AI-Native Business Operating System
- **Agentic control plane:**
  - intent understanding and Agent Planner (`agent_planner.py`);
  - Agent Registry and SDK (`registry.py`, 22 manifests, template);
  - evidence validator;
  - policy / governance gate and human approval gate;
  - action manager (auditable state machine);
  - decision records (Decision Memory);
  - learning manager (validated, approver-gated, versioned rules);
  - twin states (current / forecast / what-if / target);
  - execution traces with cost and an admin view.
- **Agents:** Business Orchestrator (main session) + 17 domain agents generated from manifests. The 4 v6.1 tier agents are kept with the spec §3 purposes. Per-invocation model routing; least privilege; the single-writer rule; autonomy L0–L3.
- **New skills:** business-orchestrator, decision-intelligence, solution-architecture, action-center, platform-admin. All 25 v6.1 skills are preserved and mapped to agents.
- **Security:** tenant-bound memory, RBAC with inheritance, ABAC, data clearance, action catalog with floors, `<data>`-wrapped packets, injection scan.
- **Fixes:** graph builder name overwrite (v6 defect); planner intent priority ("why…behind" beats topic words).
- **Tests:** 30-scenario offline suite + V6.1 regression (30/30, 8/8); 3 new live eval cases (Sanofi growth, prompt injection, challenge mode).
- **Docs:** architecture, control plane, agents, governance, observability and cost, migration map, V7 report.

## 6.1.0-beta.1 — Delegation made explicit and testable
- **Delegation protocol** (`references/delegation-protocol.md`): router → packet → Agent tool (scoped name) → wait → `reply_check.py` → escalate or accept → the main session writes memory. Added to all 25 skills; 7 skills have delegation maps.
- **New scripts:** `handoff_packet.py` (compact, tier-sized context for agents) and `reply_check.py` (reply contract, labels, decisions, invented-number guard, escalation).
- **Agents:**
  - `skills:` preloads (business-memory; pricing for the strategist);
  - `disallowedTools: Agent, Write, Edit` (one writer; no agent-to-agent escalation);
  - Read/Grep/Glob(/Skill) only; `maxTurns`; `omitClaudeMd` for the light tier;
  - reply contract in each prompt.
- **Eval suite** (`evals/`, `claude plugin eval` format): 5 delegation cases with a shared memory fixture.
- **Tests:** `tests/validate_strict.py` and `tests/run_agent_tests.sh`.
- **Docs:** docs/12 (agents and delegation); Cowork support confirmed; chat limits stated.

## 6.0.0-beta.1 — Adaptive Growth Intelligence OS (context + memory + routing)
- **New skills:** business-context-discovery (Layer 0), business-memory (Memory Graph), market-intelligence, executive-command-center (CEO / Investor / Owner).
- **New engines:**
  - context_discovery: 10 business models; seller vs customer industry; multi-dimension scale; confidence gate.
  - memory_graph: temporal facts, graph, ledger, stateful alerts, sources, runs, summaries, preferences, compression, conflicts.
  - graph_build, delta_engine: recognition, composite keys, re-analysis map.
  - model_router: T0–T4, escalation, surface bindings.
  - kpi_engine: adaptive; supported-only.
  - command_center: memory-aware HTML.
- **New `agents/`:** growth-light (haiku), growth-analyst (sonnet), growth-strategist (opus), growth-expert (fable).
- **All 25 skills** run the 12-step intelligence loop and write back to memory. Business-watch is stateful; the briefing is memory-aware; data-intelligence recognizes datasets and tracks source freshness; pricing checks decisions in force; win-loss records outcomes and learnings.
- **Guardrails v6:** §17 memory governance, §18 routing transparency, §19 decisions in force.
- **Test evidence:** a two-review test on the test workbook, with 10 defects found and fixed (docs/10).

## 5.0.0-beta.1 — AI-Native Growth Intelligence & Action Platform
- **Blueprint** (`docs/00–12`): v4 assessment and gap analysis, v5 architecture, capability map, taxonomy, shared services, Orchestrator / Twin / Opportunity Engine / Growth Graph designs, analytics and predictive architecture, governance, measurement, prioritization (13 criteria), P0–P3, Top 20, first-10 specifications, MVP → Pilot → Production. The v4 blueprint is archived.
- **New P0 services**: customer-digital-twin (replaces account-360), growth-signal-orchestrator, business-intelligence-copilot, win-loss-intelligence, knowledge-intelligence.
- **New and consolidated P1 engines**:
  - growth-opportunity-discovery (new);
  - relationship-intelligence (was buying-committee; adds account and portfolio executive intelligence);
  - competitive-intelligence (new, with early warning);
  - pricing-intelligence (was deal-desk; Deal Desk mode kept);
  - business-watch (new).
- **Consolidated**: deal-risk-intelligence and deal-strategy-win-plan are retired into deal-intelligence (batch mode plus method references).
- **Enhanced**:
  - deal-intelligence: learning loop, pricing, batch mode;
  - daily-growth-briefing: orchestrator patterns, watches, Next-Best-Account;
  - account strategist: twin-based, composed chain, account economics section;
  - renewal radar: retention focus;
  - pipeline-forecast: win/loss calibration;
  - data-intelligence: knowledge and signals;
  - scenario-planner: capacity scenarios.
- **New engines**: twin_update, signal_correlator, driver_tree, winloss_analyzer, competitive_watch, pricing_model (confounding detection), opportunity_scorer, watch_evaluator, knowledge_catalog.
- **Shared**: guardrails v5 (§15 model monitoring, §16 persistent state), orchestration v5 (routing, composition rules, backward compatibility), signal vocabulary, account_state v2.0, NBA weights, measurement Baseline → AI-assisted → Delta → Impact.

## 4.0.0-beta.1 — AI-Native Growth & Sales Intelligence Platform
- **Renamed plugin** to `growth-intelligence-platform`. It is repositioned as a System of Intelligence + System of Action above any application.
- **Blueprint** (`docs/01–12`): competitive capability map vs Sales Cloud in Claude, growth taxonomy, data, analytics, predictive, plugin and tool, orchestration, governance, measurement, Top 20, first-5 specifications (24-item standard), roadmap.
- **New skills:**
  - `deal-intelligence`: Deal Review → Strategy → Close Plan → Execution.
  - `daily-growth-briefing`: proactive intelligence.
- **Rebuilt skills:**
  - `data-intelligence` (was `sales-data-intelligence`): universal data layer.
  - `pipeline-forecast-intelligence` (was `forecast-integrity-analyst`): governance plus what-if.
- **Updated skill:** `account-intelligence-swot-planning` now follows Signals → Patterns → Risks → Opportunities → Predictions → Actions, takes cross-functional inputs, and updates automatically on material change.
- **New scripts:**
  - `entity_resolver.py`: cross-source matching, duplicates, conflicts, staleness.
  - `pipeline_whatif.py`: pipeline analytics and deal-level scenarios with common random numbers.
  - `signal_ranker.py`: role-aware ranking.
  - `normalize.py` extended to 10 entities.
- **Guardrails v4:** ABAC, §13 prompt-injection protection, §14 tool-use controls (bulk-action confirmation, no chained actions).
- **New shared references:** `orchestration.md` (routing and composition rules) and `measurement-framework.md` (existing vs assisted benchmark).

## 3.1.0-beta.1 — AI Account Strategist
- **New skill: `account-intelligence-swot-planning`**, covering:
  - 360-degree account intelligence;
  - evidence-based SWOT (Evidence → Interpretation → Business impact → Confidence → Response, with an anti-generic test);
  - predictive account intelligence (12 predictions);
  - whitespace sizing;
  - a 9-dimension risk dashboard;
  - a strategic account plan with a 30/60/90-day action plan;
  - portfolio prioritization;
  - Account Change Intelligence;
  - six output modes: executive brief, strategic plan, account review, deep dive, change report, portfolio.
- **New scripts:**
  - `whitespace_matrix.py`: peer-benchmarked potential; refuses to size offerings with thin peer evidence.
  - `account_prioritizer.py`: drivers plus rank stability under changed weights.
  - `account_change_diff.py`: material-change detection and a strategy-review flag.
- **New contracts:** `account_state` v1.0 (snapshots for continuous monitoring) and `account_plan` v1.0.
- **Measurement protocol:** baseline, then targets of −70% research effort, −50% preparation time, ≥ 90% evidence coverage, ≥ 90% risk-detection accuracy.

## 3.0.0-beta.1 — Application-agnostic intelligence layer
- **Principle:** bring your data, connect your systems, Claude provides the intelligence. Skills no longer assume a particular vendor.
- **New Connect stage** in every skill: Connect → Understand → Analyze → Predict → Recommend → Act → Learn.
- **Output layers** are now Data → Metric → Insight → Prediction → Recommendation → Action (guardrails v3 §1).
- **New shared references:**
  - `semantic-model.md`: canonical entities and field maps across Salesforce, Dynamics, HubSpot, SAP, Oracle, ServiceNow, Workday, and spreadsheets; identity resolution; system-of-record rules; lineage.
  - `connect-protocol.md`: discover, authorize per system, profile, normalize, resolve identities.
  - `analytics-methods.md`: embedded descriptive, diagnostic, predictive, prescriptive, and scenario methods.
  - `skill-design-card.md` in every skill: the 20-item design standard.
- **New skills:**
  - `data-intelligence`: Excel and file intelligence.
  - `scenario-planner`: what-if analysis; best, base, and worst cases; sensitivity; capacity and pricing scenarios.
  - `customer-digital-twin`: cross-system account view.
- **New scripts:**
  - `data_profiler.py`: types, quality, duplicates, outliers, entity detection, sheet relationships, sensitive-column masking.
  - `normalize.py`: any source to canonical fields, with confidence scores, stage-ladder mapping, day-first/month-first date detection that stops on ambiguity, and lineage.
  - `ts_forecast.py`: naive, seasonal-naive, or Holt-Winters, chosen by backtest, with empirical intervals.
  - `scenario_model.py`: driver-based scenarios with a sensitivity tornado.
- **Guardrails v3:** per-system authorization (access is never inferred), source attribution for every metric, data validation before analysis, masking of identifiers found in files, assumptions and limitations required on every prediction.
- **Vendor-specific wording removed** from all skills.

## 2.0.0-beta.1 — Predictive intelligence layer
- Added `deal-intelligence`, prediction standards, the learning ledger, and the predictive scripts.

## 1.0.0-beta.1
- Initial 10 skills.
