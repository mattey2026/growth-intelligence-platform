# 14. V7 Release Report

Status legend:
- **IMPLEMENTED**: exists in the package and is exercised by tests.
- **PARTIAL**: exists, with stated gaps.
- **DESIGNED**: specified, not built.
- **PLANNED**: roadmap.

## 1. Retained from V6.1 (nothing removed)
All **25 skills**, all **4 reasoning-tier agents** (growth-light / analyst / strategist / expert; T4 never by default), the **memory graph** (facts, graph, ledger, stateful alerts, sources, runs, summaries, compression), **context discovery**, **delta engine**, **adaptive KPIs**, **command center**, **delegation protocol**, **19 contracts**, and **32 analytics scripts**. The V6.1 regression passes 8/8. See docs/13 for the component-by-component map.

## 2. Enhanced
- **Memory:** optional tenant binding; `rules` table for validated learning.
- **Graph builder:** bug fix. Account names were being overwritten by IDs, a v6 defect found by the V7 planner.
- **Handoff packet v2:** agent contract, `<data>` provenance wrappers, and evidence and action fields.
- **Reply checking:** superseded by the evidence validator (the old script is kept).
- **Model routing:** tier passed per invocation to domain agents.
- **All 30 skills:** carry a V7 operating model that names the agents using them.
- **Tier agents:** purposes set per spec §3.

## 3. New agents (IMPLEMENTED as manifests + generated plugin agents)
The Business Orchestrator (main session) plus 17 domain agents:

| Group | Agents |
|---|---|
| Account and growth | account-intelligence, opportunity, deal-strategy, relationship, customer-growth |
| Commercial | pricing-commercial |
| External intelligence | competitive-intelligence, market-intelligence, research |
| Meetings and forecasting | meeting-intelligence, pipeline-forecast |
| Decisions and solutions | executive-decision, solution-architect |
| Execution | action-workflow |
| Platform | data-intelligence, governance-risk, outcome-learning |

Each has all 18 contract fields, least-privilege tools, blocked Agent/Write/Edit/Bash, limited preloads, and autonomy L0–L2. 21 agent files in total, including the 4 tiers.

## 4. New platform services
| Service | File | Status |
|---|---|---|
| Intent understanding + Agent Planner | `agent_planner.py` | IMPLEMENTED (rule-based: 22 intents, 6 modes; LLM refinement by instruction) |
| Agent Registry + SDK | `registry.py`, manifests, `_template.yaml` | IMPLEMENTED |
| Agent / skill / tool router | Planner + manifests + generated allowlists | IMPLEMENTED |
| Execution manager | Orchestrator skill procedure (dependencies, parallel groups, waits) | PARTIAL: instruction-driven, not a runtime engine |
| Evidence validator | `evidence_validator.py` (contract, provenance, fact vs inference, external sourcing, cross-agent conflicts, injection scan) | IMPLEMENTED |
| Policy / governance gate + approval gate | `policy_gate.py`, `action-catalog.yaml`, `tenant-policy` | IMPLEMENTED; enforcement is procedural (see risks) |
| Action manager | `action_manager.py` (state machine, audit log) | IMPLEMENTED; connectors execute |
| Decision intelligence | skill + `decision_record.py` (owner-only approval → decision in force) | IMPLEMENTED |
| Outcome tracker + learning manager | ledger outcomes, `learning_manager.py` (candidate → validated → adopted with approver; never automatic) | IMPLEMENTED |
| Digital twin states | `twin_state.py` (CURRENT / FORECAST / WHAT-IF / TARGET) | PARTIAL: states are stored and viewed; forecasts must be written by skills |
| Observability + cost | `trace.py` (spans, summaries, cost per query / agent / recommendation / action, admin HTML) | IMPLEMENTED (tokens estimated; prices configurable) |
| New skills | business-orchestrator, decision-intelligence, solution-architecture, action-center, platform-admin | IMPLEMENTED |

## 5. What remains incomplete
| Item | Status |
|---|---|
| **Live multi-agent runs.** The 8 eval cases (including Sanofi) are ready but **not run here**: they need your Claude Code credentials. | PARTIAL |
| Per-agent evaluation scoring pipeline (the metrics are defined; scores are not auto-computed) | DESIGNED |
| Proactive monitoring on a schedule (business-watch is stateful, but nothing runs it periodically) | PARTIAL |
| Multi-tenant service, billing, and admin UI beyond the static HTML | DESIGNED |
| LLM-based intent classifier with an eval set (today: rules + orchestrator refinement) | PLANNED |
| Consumer (D2C/B2C) engines (cohort retention, marketing mix) | PLANNED |
| Column-level lineage and automatic retention purge | PLANNED |

## 6. Known technical limitations
- **Agents run only in Claude Code and Cowork.** In claude.ai chat the orchestrator runs agent steps inline under each manifest's contract, with no model switching.
- **The orchestrator's control loop is followed by the model through skill instructions.** No platform runtime forces the step order. The scripts enforce their own invariants (action state machine, owner approval, learning validation, tenant binding, registry validation).
- The per-invocation model override depends on Claude passing `model` when delegating. `CLAUDE_CODE_SUBAGENT_MODEL_FORCE` overrides everything.
- The `skills:` preload format for plugin skills is not documented. Agents fall back to the Skill tool.
- The planner is regex-based and English-only. Unusual phrasing falls back to account intelligence or business health.
- SQLite memory is single-writer. It suits one user or team, not concurrent enterprise load.
- Token counts are estimates unless the runtime reports usage.

## 7. Security risks
1. **Gate enforcement is procedural.** A connector write the model performs *without* calling `policy_gate.py` is not blocked by the platform; Claude's own permission prompts and connector approvals still apply. **V8 #1:** a plugin `PreToolUse` hook that blocks connector write tools unless an approved `action_log` entry exists.
2. **The injection scan is pattern-based.** Novel phrasings can pass. The structural defenses (data wrapping, read-only agents, gate before action) are the main protection.
3. **Memory and trace files on disk contain business data** and are not encrypted by the platform. Rely on disk and warehouse encryption and access control.
4. **Data sensitivity labels must come from the connectors or data owners.** Unlabelled PII is not detected.
5. **Tenant isolation is per file.** A misconfigured shared path would put two tenants in one directory (each memory file still refuses a foreign tenant).

## 8. Performance risks
- A full Sanofi-style plan has 18 steps and about 10 agents. Parallel groups help, but end-to-end latency is minutes, not seconds.
- In interactive sessions agents run in the background by default, and the orchestrator must wait for completion notifications.
- Preloaded skills add about 2–7k tokens per agent invocation.
- SQLite contention under concurrent writers.

## 9. Cost risks
- Opportunity discovery is the most expensive intent: T3 steps plus web research. A test trace estimated about 43 relative units per recommendation.
- Eval runs are real model calls: 8 cases × 3 runs, plus judges.
- Without a price table, costs are relative units, not currency.
- **Mitigations in place:** memory reuse (a 76% cost cut in the reuse test), delta-only re-analysis, T0 code, conditional-only T4, limited preloads, and compact packets.

## 10. Recommended V8 roadmap
1. **Hard enforcement hook:** a `PreToolUse` gate on connector writes, plus a `SubagentStart/Stop` trace hook.
2. **Run and score the live evals.** Publish per-agent scores into the registry and gate releases on them.
3. **Scheduled proactive intelligence**, using scheduled tasks where the product supports them.
4. **Warehouse-backed memory and graph** (the same schema) for concurrency and multi-tenant scale.
5. **An LLM intent classifier** with a labelled evaluation set; keep the rules as a fallback.
6. **Measured token and cost metering** from runtime usage, plus a configured price table.
7. **Consumer engines** and industry packs (pharma, banking, retail) as manifests plus skills.
8. **Tenant service:** users, roles, and connectors per tenant; a billing export from traces.

## Verification at release
| Check | Result |
|---|---|
| `tests/run_offline.py` | 30/30 scenarios, 8/8 V6.1 regression |
| `registry.py validate` | OK (22 agents, all 30 skills reachable) |
| Strict YAML | OK |
| `claude plugin validate .` and `./agents` | Passed (Claude Code 2.1.284) |
