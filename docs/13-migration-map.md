# 13. Migration Map: V6.1 → V7

Generated from `v61_inventory.json` (the inventory of the v6.1 package: 25 skills, 4 agents, 32 distinct scripts / 230 copies, 34 shared references, 19 contracts) and the V7 registry.

| V6.1 capability | V7 location | Status | Reason |
|---|---|---|---|
| skill `account-intel-outreach` | skills/account-intel-outreach · used by opportunity-agent | PRESERVED | unchanged v6.1 logic; now reached through domain agents |
| skill `account-intelligence-swot-planning` | skills/account-intelligence-swot-planning · used by account-intelligence-agent, opportunity-agent | PRESERVED | unchanged v6.1 logic; now reached through domain agents |
| skill `business-context-discovery` | skills/business-context-discovery · used by business-orchestrator, data-intelligence-agent | PRESERVED | unchanged v6.1 logic; now reached through domain agents |
| skill `business-intelligence-copilot` | skills/business-intelligence-copilot · used by business-orchestrator, executive-decision-agent | ENHANCED | cross-functional intent; decision agent |
| skill `business-memory` | skills/business-memory · used by account-intelligence-agent, action-workflow-agent, business-orchestrator, competitive-intelligence-agent, customer-growth-agent, data-intelligence-agent, deal-strategy-agent, executive-decision-agent, governance-risk-agent, growth-analyst, growth-expert, growth-strategist, market-intelligence-agent, meeting-intelligence-agent, opportunity-agent, outcome-learning-agent, pipeline-forecast-agent, pricing-commercial-agent, relationship-agent, research-agent, solution-architect-agent | ENHANCED | learning_manager (validated rules), tenant binding, graph merge fix |
| skill `business-watch` | skills/business-watch · used by business-orchestrator | ENHANCED | proactive signals routed via orchestrator |
| skill `competitive-intelligence` | skills/competitive-intelligence · used by competitive-intelligence-agent, deal-strategy-agent, opportunity-agent | PRESERVED | unchanged v6.1 logic; now reached through domain agents |
| skill `customer-digital-twin` | skills/customer-digital-twin · used by account-intelligence-agent, customer-growth-agent | ENHANCED | twin_state.py CURRENT→FORECAST→WHAT-IF→TARGET |
| skill `daily-growth-briefing` | skills/daily-growth-briefing · used by business-orchestrator | PRESERVED | unchanged v6.1 logic; now reached through domain agents |
| skill `data-intelligence` | skills/data-intelligence · used by data-intelligence-agent | ENHANCED | agent-driven validation before high-impact plans |
| skill `deal-intelligence` | skills/deal-intelligence · used by deal-strategy-agent, pipeline-forecast-agent | PRESERVED | unchanged v6.1 logic; now reached through domain agents |
| skill `executive-command-center` | skills/executive-command-center · used by business-orchestrator | ENHANCED | role altitude (seller→investor) via orchestrator |
| skill `growth-opportunity-discovery` | skills/growth-opportunity-discovery · used by customer-growth-agent, opportunity-agent | PRESERVED | unchanged v6.1 logic; now reached through domain agents |
| skill `growth-signal-orchestrator` | skills/growth-signal-orchestrator · used by customer-growth-agent | ENHANCED | customer-growth agent; exposure step for market events |
| skill `knowledge-intelligence` | skills/knowledge-intelligence · used by account-intelligence-agent, competitive-intelligence-agent, opportunity-agent, research-agent, solution-architect-agent | PRESERVED | unchanged v6.1 logic; now reached through domain agents |
| skill `market-intelligence` | skills/market-intelligence · used by market-intelligence-agent, opportunity-agent | PRESERVED | unchanged v6.1 logic; now reached through domain agents |
| skill `meeting-follow-through` | skills/meeting-follow-through · used by meeting-intelligence-agent, relationship-agent | PRESERVED | unchanged v6.1 logic; now reached through domain agents |
| skill `meeting-intelligence-brief` | skills/meeting-intelligence-brief · used by meeting-intelligence-agent | PRESERVED | unchanged v6.1 logic; now reached through domain agents |
| skill `pipeline-forecast-intelligence` | skills/pipeline-forecast-intelligence · used by pipeline-forecast-agent | PRESERVED | unchanged v6.1 logic; now reached through domain agents |
| skill `pricing-intelligence` | skills/pricing-intelligence · used by deal-strategy-agent, pricing-commercial-agent | ENHANCED | decision records; Pricing & Commercial agent at T3 |
| skill `relationship-intelligence` | skills/relationship-intelligence · used by account-intelligence-agent, deal-strategy-agent, meeting-intelligence-agent, relationship-agent | PRESERVED | unchanged v6.1 logic; now reached through domain agents |
| skill `renewal-expansion-radar` | skills/renewal-expansion-radar · used by customer-growth-agent | PRESERVED | unchanged v6.1 logic; now reached through domain agents |
| skill `rfp-response-composer` | skills/rfp-response-composer · used by solution-architect-agent | PRESERVED | unchanged v6.1 logic; now reached through domain agents |
| skill `scenario-planner` | skills/scenario-planner · used by executive-decision-agent, pipeline-forecast-agent, pricing-commercial-agent | ENHANCED | twin WHAT-IF states; decision agent |
| skill `win-loss-intelligence` | skills/win-loss-intelligence · used by competitive-intelligence-agent, deal-strategy-agent, outcome-learning-agent | ENHANCED | feeds learning_manager candidates |
| agent `growth-analyst` (sonnet) | agents/growth-analyst.md (generated from registry manifest) | PRESERVED + ENHANCED | kept as reasoning tier; V7 purpose per spec §3; manifest contract |
| agent `growth-expert` (fable) | agents/growth-expert.md (generated from registry manifest) | PRESERVED + ENHANCED | kept as reasoning tier; V7 purpose per spec §3; manifest contract |
| agent `growth-light` (haiku) | agents/growth-light.md (generated from registry manifest) | PRESERVED + ENHANCED | kept as reasoning tier; V7 purpose per spec §3; manifest contract |
| agent `growth-strategist` (opus) | agents/growth-strategist.md (generated from registry manifest) | PRESERVED + ENHANCED | kept as reasoning tier; V7 purpose per spec §3; manifest contract |
| `reply_check.py` | still shipped in every v6.1 skill | PRESERVED (superseded) | `evidence_validator.py check` is the V7 path; kept for backward compatibility |
| `graph_build.py` | all skills | ENHANCED (bug fix) | later sheets keyed on the same ID now merge instead of overwriting names (v6 defect found by V7 planner) |
| `memory_graph.py` | all skills | ENHANCED | optional tenant binding (`GROWTH_TENANT`); unbound v6.1 files keep working |
| `handoff_packet.py` | all skills | ENHANCED (v2) | agent contract, `<data>` provenance wrappers, action/evidence fields; v6.1 calls unchanged |
| 32 other scripts (230 copies) | unchanged locations | PRESERVED | zero version drift at inventory |
| 19 data contracts (account_health, account_plan, account_pov, bi_answer, briefing, competitive_view, …) | unchanged | PRESERVED | agents return `agent_result_v1` which embeds existing contracts |
| Nothing | — | DEPRECATED | no v6.1 capability removed |

**New in V7:** 5 skills (business-orchestrator, decision-intelligence, solution-architecture, action-center, platform-admin), 17 domain agents + 1 main-session supervisor, 10 control-plane scripts, registry, policy, and evals.
