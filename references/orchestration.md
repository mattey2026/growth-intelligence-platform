# Cross-Skill Orchestration (v6.0)

**Every chain starts with Layer 0 and memory:** business-context-discovery (reuse the profile) → business-memory (recall and delta) → the lead skill → … → business-memory (write). See `intelligence-loop.md`.

**Principle:** Any Data → Any Application → Unified Context → Analytics → Prediction → Reasoning → Recommendation → Decision → Authorized Action → Outcome → Learning.

The user states an outcome. Claude plans the minimum chain of skills, passes **contracts** between them, and stops at every approval point.

## Layers
| Layer | Components |
|---|---|
| Platform services (P0) | data-intelligence · knowledge-intelligence · customer-digital-twin · growth-signal-orchestrator · win-loss-intelligence · business-intelligence-copilot · prediction ledger · shared scripts |
| Growth engines (P1) | growth-opportunity-discovery · relationship-intelligence · competitive-intelligence · pricing-intelligence · business-watch |
| Workflow skills | deal-intelligence · pipeline-forecast-intelligence · account-intelligence-swot-planning · renewal-expansion-radar · daily-growth-briefing · meeting-intelligence-brief · meeting-follow-through · scenario-planner · account-intel-outreach · rfp-response-composer |

## Routing (the objective decides the lead skill)
| The objective mentions or implies | Lead | Typical chain |
|---|---|---|
| A new or updated dataset or connection | business-context-discovery → data-intelligence | delta_engine recognize → reuse or partial re-analysis |
| "What changed / what did we decide / what did we predict / what have we learned" | business-memory | |
| Executive dashboard, "how are we doing", board or investor view | executive-command-center | memory → KPI engine → forecast → orchestrator → copilot |
| Market, industry, benchmarks, "how do we compare" | market-intelligence | profile → web research → memory |
| File, dataset, data quality, reconcile | data-intelligence | → the domain skill for the detected entity |
| Policy, contract, "latest version", which document | knowledge-intelligence | |
| "Why is X behind / what's driving" | business-intelligence-copilot | → pipeline, deal, win-loss, twin, pricing engines |
| An account: 360, what changed, why | customer-digital-twin | → orchestrator (patterns) |
| An account: plan, SWOT, strategy, QBR | account-intelligence-swot-planning | twin → relationship → competitive → opportunity → economics → deal → plan |
| "Where can we grow", whitespace, cross-sell | growth-opportunity-discovery | twin, orchestrator, competitive, knowledge |
| A deal: review, win, close plan; audit pipeline | deal-intelligence | relationship → pricing → competitive → win-loss |
| Quarter, forecast, what-if deals | pipeline-forecast-intelligence | deal-intelligence (batch) → scenario-planner |
| Discount, price, quote, approval | pricing-intelligence | deal-intelligence (base win probability) |
| Competitor | competitive-intelligence | win-loss → opportunity (displacement) |
| Why we win or lose | win-loss-intelligence | → feeds models |
| Stakeholders, executive coverage | relationship-intelligence | |
| "Connect the dots", cross-functional risk | growth-signal-orchestrator | → the triggered skills |
| "Watch / alert me when" | business-watch | → the investigate_with skills |
| "What should I do today", where to spend time | daily-growth-briefing | orchestrator + watches + Next-Best-Account |
| Churn, renewal, health | renewal-expansion-radar | twin → orchestrator |
| Hiring, capacity, targets, driver what-if | scenario-planner | |
| Meetings | meeting-intelligence-brief / meeting-follow-through | twin; deal_delta |

## Composition rules
1. **Confidence propagates down**: a combined conclusion is no stronger than its weakest material input.
2. **Coverage propagates**: every missing source anywhere in the chain is listed.
3. **Actions stay with the owning skill**, under its approval step.
4. **Reuse before recompute**: use a fresh contract (the same day) instead of retrieving again.
5. **Cross-functional influence**: when a signal from service, finance, marketing, or product changes a sales conclusion, show it with its source.
6. **Write back**: skills that assess an account update the twin (a snapshot) and emit signals, so the platform's understanding accumulates.
7. **Learning**: outcomes flow back through win-loss (deals), the ledger (predictions), and pattern precision (orchestrator).

## Backward compatibility (v4 → v5)
| v4 skill | v5 destination |
|---|---|
| account-360-intelligence | customer-digital-twin |
| buying-committee-intelligence | relationship-intelligence (deal mode) |
| deal-desk-precheck | pricing-intelligence (Deal Desk mode) |
| deal-risk-intelligence | deal-intelligence (batch mode) + references/deal-risk-method.md |
| deal-strategy-win-plan | deal-intelligence + references/deal-strategy-method.md |

Contracts `deal_risk`, `commercial_check`, `buying_committee`, and `account_state` v1.0 are still produced or accepted.
