# 3. Agents

**Source of truth:** `registry/manifests/<id>.yaml`. Each manifest carries all 18 contract fields plus version, status, owner, runtime, autonomy, and evaluation. `registry.py build` generates `agents/*.md` and `registry/agent-registry.json`.

| Agent | Default → max tier | Autonomy | Primary skills |
|---|---|---|---|
| business-orchestrator *(main session)* | T2 → T4 | L1 | business-orchestrator, action-center, … |
| account-intelligence-agent | T2 → T3 | L0 | customer-digital-twin, account-intelligence-swot-planning |
| opportunity-agent | T2 → T3 | L1 | growth-opportunity-discovery, account-intelligence-swot-planning |
| deal-strategy-agent | T2 → T4 | L1 | deal-intelligence, relationship-intelligence |
| relationship-agent | T2 → T3 | L1 | relationship-intelligence |
| pricing-commercial-agent | T3 → T4 | L1 | pricing-intelligence, scenario-planner |
| customer-growth-agent | T2 → T3 | L1 | renewal-expansion-radar, customer-digital-twin |
| competitive-intelligence-agent | T2 → T3 | L0 | competitive-intelligence (+ web) |
| market-intelligence-agent | T2 → T3 | L0 | market-intelligence (+ web) |
| research-agent | T1 → T2 | L0 | knowledge-intelligence (+ web) |
| meeting-intelligence-agent | T2 → T3 | L1 | meeting-intelligence-brief, meeting-follow-through |
| pipeline-forecast-agent | T2 → T3 | L0 | pipeline-forecast-intelligence, deal-intelligence |
| executive-decision-agent | T3 → T4 | L1 | decision-intelligence, scenario-planner |
| solution-architect-agent | T3 | L1 | solution-architecture, knowledge-intelligence |
| action-workflow-agent | T1 → T2 | L2 | action-center |
| data-intelligence-agent | T1 → T2 | L0 | data-intelligence, business-context-discovery |
| governance-risk-agent | T2 → T3 | L0 | platform-admin |
| outcome-learning-agent | T2 → T3 | L1 | business-memory, win-loss-intelligence |
| growth-light / analyst / strategist / expert | fixed T1 / T2 / T3 / T4 | L0 | v6.1 reasoning tiers (T4 never by default) |

## Runtime rules (enforced in the generated files and by `registry.py validate`)
- **Tools:** Read, Grep, Glob, Skill; plus WebSearch and WebFetch for the research, market, and competitive agents only.
- **Always blocked:** Agent, Write, Edit, Bash. The single-writer rule means agents cannot act, write memory, or start other agents.
- **Autonomy:** agents are capped at L2 (they prepare actions). L3 execution happens only in the main session, and only under a tenant policy.
- **Preloading:** only the primary skills are preloaded (cost control); agents load the others on demand, within their allowlist.

## Autonomy levels
| Level | Name | Rule |
|---|---|---|
| L0 | Analyze | Read, analyse, explain |
| L1 | Recommend | Recommend and prepare; human approval required |
| L2 | Controlled | Predefined low-risk actions |
| L3 | Policy-bound | Automatic, only for low-risk internal catalog actions with `auto_execute_low_risk` enabled |

External communications, pricing, contracts, forecasts, and stage changes always require approval. `pricing.commit` and `contract.*` are human-only.

## SDK: adding a customer-specific agent
Copy `registry/manifests/_template.yaml`, fill it in, add eval cases, then run `registry.py validate` → `build` → `claude plugin validate .`. Customer agents (a Sanofi account agent, a pharma regulatory agent, an SAP finance agent…) reuse existing skills and pass through the same gate. The core platform does not change.
