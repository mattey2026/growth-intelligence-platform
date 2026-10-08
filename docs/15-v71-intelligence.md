# V7.1: Marketing, Financial and Competitive Thread intelligence

This document summarizes the implemented behaviour. The source of truth is the skill files and scripts named here.

| Capability | Skill / agent | Engine | Tests |
|---|---|---|---|
| Marketing Intelligence | marketing-intelligence / marketing-intelligence-agent | marketing_signals.py | MKT 1–11 |
| Financial Intelligence | financial-intelligence / financial-intelligence-agent | financial_intel.py | FIN 1–13 |
| Competitive Threads | competitive-thread-intelligence / competitive-thread-agent | competitive_threads.py | THR 1–18, 7b |
| Cross-domain correlation | growth-signal-orchestrator | cross_domain_correlator.py | COR 1–11 |
| Orchestration and discovery | business-orchestrator | agent_planner.py | ORC 1–8 |
| Digital Twin domains | customer-digital-twin | twin_state.py, domain_delta.py | TWN 1–5 |
| Memory objects | business-memory | memory_graph.py | MEM 1–6 |
| Evidence and governance | platform-admin, policy | evidence_validator.py, policy_gate.py | EVG 1–10 |
| Observability | platform-admin | trace.py | OBS 1–3 |
| Account plan and opportunities | account-intelligence-swot-planning, growth-opportunity-discovery | account_plan_builder.py, opportunity_builder.py | XF |

## Memory model
**Typed domain objects** (table `domain_objects`; `memory_graph.py obj-put` / `obj-query`):
- MarketingSignal, AccountEngagement, CampaignInfluence;
- FinancialMetric, FinancialSignal;
- CompetitiveEvent, CompetitiveThread, CompetitiveHypothesis, CompetitiveOutcome;
- CrossDomainPattern.

Each object carries obj_type, tenant, account_id, competitor_id, opportunity_id, observed_at, recorded_at, source, source_date, confidence, claim_type, and data. Objects are queryable by account, competitor, opportunity, and time, and only within the bound tenant.

**Competitive threads** (tables `competitive_threads` and `thread_signals`, maintained by `competitive_threads.py`) persist across sessions. Their schema is in `skills/competitive-thread-intelligence/SKILL.md`.

**Twin snapshots** (table `twin_snapshots`) hold the eight state domains. FORECAST, WHAT_IF, and TARGET live in the ledger as `scenario` rows.

## Confidence and evidence
Each engine documents its confidence model in its SKILL.md. All pattern and opportunity outputs are HYPOTHESIS. Values are sized only with a stated basis (INTERNAL_ESTIMATE or FACT_BASED_RANGE). Financial numbers trace to a source fact or a formula.
