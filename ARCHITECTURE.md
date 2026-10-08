# Architecture (V8)

## Front door: starter prompts (V8)
```text
USER INTENT ─▶ STARTER PROMPT (card · menu · /command · dashboard suggestion · typed text)
                    │  prompt_engine.py: catalog + persona + context (account, competitor…) + live signals
                    ▼
            BUSINESS ORCHESTRATOR  agent_planner.py: typed text is classified; a clicked prompt or command passes --capability
                    ▼
            AGENT (registry discovery) ─▶ SKILL ─▶ DATA · MEMORY · TWIN ─▶ INTELLIGENCE ─▶ DECISION ─▶ ACTION ─▶ OUTCOME
```
- **One router.** Prompts, slash commands and dashboard cards add no logic; they reach the same orchestrator, governance and evidence rules as typed text.
- **Single source of truth.** `skills/growth-discovery/references/starter-prompts/*.yaml` generates the slash commands, the "Starter prompts" section in each SKILL.md and the dashboard's discovery block. Tests enforce that they stay in sync.
- **V8 orchestrator changes:**
  - thirteen capability intents, whose lead agent is discovered from the registry by the skill it preloads;
  - priority patterns ("this deal" outranks "customer health"; "what if…" is always a scenario);
  - the `--capability` hint.


## Dashboard Intelligence layer (V7.2)
```text
User → Claude → Business Orchestrator ──(dashboard intent)──▶ dashboard-intelligence-agent (T2: persona, entity, objective, domains)
                       │
                       ├─ domain agents (registry discovery): account, financial, marketing, competitive-thread, relationship
                       ├─ Business Memory · Digital Twin · Delta · Growth Signal Orchestrator (T0 engines)
                       ▼
     Provider (demo_provider.py | production_provider.py) → bundle
                       ▼
     dashboard_builder.py (T0: every number, delta, facet, drill path, scenario, comparison; role restrictions applied)
                       ▼
     DASHBOARD CONTRACT  (schemas/dashboard.schema.json; renderer-independent)
                       ▼
     contract_review (agent, T2) → render_dashboard.py → Claude Artifact (Enterprise Growth Command Center)
                       ▼
     user: drill-down · cross-filter · evidence · scenarios · actions ──▶ Ask Intelligence / Request approval ──▶ Business Orchestrator ──▶ Action Center ──▶ outcome ──▶ memory
```
- **Skill** defines the dashboard intelligence and design rules. The **agent** decides the experience. The **contract** standardizes the data. The **renderer** displays it.
- **No business logic in the artifact.** Values, deltas, sentiment, facets, drill paths and scenarios all arrive in the contract. React, Next.js, portal or mobile renderers can replace the artifact unchanged.
- **One builder for demo and production.** Only the provider changes. Absent inputs are "Not available", with what they need; never zero.
- **Security before rendering.** Role data classes come from the tenant policy. Restricted data is removed from the contract.


## The closed loop
Data → Business context → Memory → Digital twin → Delta → Signals → Cross-domain correlation → Prediction → Opportunity / risk → Decision → Human governance → Action → Outcome → Learning → Memory.

It runs across marketing, finance, competition, customer, account, market, relationships, product, operations, pipeline, deals, pricing, contracts, and opportunities.

## What V7.1 added, and why
| Component | Why | Integration point |
|---|---|---|
| `marketing_signals.py` (marketing-intelligence skill and agent) | Marketing activity was invisible at account level; attribution was often overstated | Output feeds P1 and P5, the account plan (section 4), opportunities (why now), and memory |
| `financial_intel.py` (financial-intelligence skill and agent) | Account strategy lacked the customer's own financial story; LLM arithmetic is unreliable | Output feeds P2, P3 and P5, the account plan (sections 2–3), decisions, and memory; all math is T0 |
| `competitive_threads.py` (competitive-thread-intelligence skill and agent) | Competitor signals were isolated observations | Persistent threads feed P4, the plan (sections 7–8), opportunities (displacement), the twin, and delta |
| `cross_domain_correlator.py` | Single-domain signals miss compound patterns | Growth Signal Orchestrator; routes to agents; writes CrossDomainPattern |
| `twin_state.py` V7.1 | The twin needed explicit domains | Eight state domains; HISTORICAL / CURRENT / FORECAST / WHAT_IF / TARGET |
| `domain_delta.py` | Recompute only what changed, per domain | New, changed, deleted, corrected, and contradictory items, plus a recompute map |
| `opportunity_builder.py` | Opportunities needed cross-domain evidence and honest sizing | 11 fields; values sized only with a stated basis, otherwise unsized |
| `account_plan_builder.py` | Integrated 12-section plan with evidence per conclusion | Sections without evidence are flagged, never padded |
| `memory_graph.py` objects | Typed, queryable domain memory | `obj-put` / `obj-query` by account, competitor, opportunity, and time; tenant-scoped |
| `evidence_validator.py claims` | Evidence contract for the new outputs | Rejects fabricated financial values, fabricated marketing activity, unsupported competitor claims, and causal language on correlations |
| `agent_planner.py` discovery | New agents must be usable without code changes | Manifests declare `serves_intents`; DISABLED agents are dropped |
| `trace.py check` and V7.1 events | End-to-end traceability | request → … → outcome, with execution treated as one phase |

The account-strategy chain is: context → memory → delta → [account, relationship, market, financial, marketing, and competitive-thread agents in parallel] → correlate (T0) → opportunities (T3) → twin snapshot (T0) → 12-section plan (T3) → evidence → governance → decision framing → action prep → policy gate → memory.

---

# Architecture (v6.0)

The full documentation is in `docs/`.

```
 ANY DATA · ANY APPLICATION · ANY BUSINESS MODEL · ANY INDUSTRY · ANY SIZE
        │
 LAYER 0  business-context-discovery → Business Context Profile (persisted; reused unless contradicted)
        │
 MEMORY   business-memory: facts (temporal) · graph (nodes/edges) · ledger (predictions → decisions → actions → outcomes → learnings)
          · alerts (stateful) · sources (freshness) · summaries · preferences · run log (routing)
        │
 DELTA    delta_engine: recognize dataset → diff → re-analysis map → reuse unchanged conclusions
        │
 ROUTING  model_router: T0 code → T1 haiku → T2 sonnet → T3 opus → T4 fable (escalate on triggers only)
        │
 INTELLIGENCE  market-intelligence · data · knowledge · twin · orchestrator · BI copilot · win/loss · adaptive KPIs
        │
 DECISION & ACTION  growth engines + workflow skills; decisions in force; approval-gated actions
        │
 EXPERIENCE  executive-command-center (CEO / Investor / Owner) · daily briefing · business watch (stateful)
        │
 OUTCOME → LEARNING → UPDATED MEMORY GRAPH
```

## The loop
Every skill runs the 12 steps in `references/intelligence-loop.md`. The first question is always: **"Do I already know this, and has anything changed that would invalidate it?"**

## Components added in v6
| Kind | Component |
|---|---|
| Skills (4) | business-context-discovery · business-memory · market-intelligence · executive-command-center |
| Engines (7) | context_discovery · memory_graph · graph_build · delta_engine · model_router · kpi_engine · command_center |
| Subagents (4) | growth-light (haiku) · growth-analyst (sonnet) · growth-strategist (opus) · growth-expert (fable) |
| References | intelligence-loop · memory-model · model-routing (plus policy JSON) · adaptive-kpi-library · business-model-taxonomy · guardrails §17–19 |
