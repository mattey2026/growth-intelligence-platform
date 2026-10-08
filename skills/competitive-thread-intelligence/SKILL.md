---
name: competitive-thread-intelligence
description: Competitive Thread Intelligence — maintains persistent CompetitiveThreads in Business Memory so competitor signals about the same account and competitor form one evolving story (chronology, velocity, acceleration or weakening, counter-evidence, resolution) linked to opportunities, stakeholders, campaigns, financial, relationship and market signals, with a predicted next event, recommended actions and recorded outcome. Use for "where are competitors gaining ground", "what is Competitor X doing in this account", "is this competitive threat getting worse", "update the competitive picture", or whenever a new competitor signal arrives.
---

> Shared scripts and references live at the plugin root: `../../scripts/` and `../../references/` from this skill's folder.


# Competitive Thread Intelligence

Version 7.1 · Used by the **competitive-thread-agent** (and the deal, account, and orchestrator flows)

## The CompetitiveThread object (persistent)
Stored in the memory file (tables `competitive_threads` and `thread_signals`), tenant-scoped, and survives sessions. Fields:

`thread_id, account_id, competitor_id, thread_type, status, title, description, created_at, updated_at, first_signal, latest_signal, signal_count, signal_velocity, confidence, risk_level, opportunity_level, stakeholders, opportunities, campaigns, financial_signals, relationship_signals, market_signals, evidence, source_history, chronology, hypotheses, counter_evidence, predicted_next_event, recommended_actions, owner, outcome, outcome_date, momentum`

## Operating instructions
1. **For every new competitor signal:**
   `python ../../scripts/competitive_threads.py <db> ingest signals.json [--asof DATE]`
   This runs: signal → memory lookup → thread matching (same tenant + account + competitor + compatible family, within 180 days) → update or create → recompute (velocity, momentum, confidence, risk, prediction, actions) → persist (the thread plus `CompetitiveEvent` and `CompetitiveHypothesis` objects).
2. **Link context:** `competitive_threads.py <db> link <thread> --opportunity O --stakeholder C --campaign M --financial-signal F --relationship-signal R --market-signal S`.
3. **Read:** `get <thread>` · `query --account A | --competitor C | --opportunity O | --status S | --since D` · `snapshot --account A` (for the twin and delta).
4. **Close:** `outcome <thread> --outcome won|lost|competitor_exited|no_decision --date D --evidence "…"`. This stores a `CompetitiveOutcome` and the prediction made at close, for learning.
5. **Validate** the agent's interpretation with `evidence_validator.py claims` (unsupported competitor claims are rejected).

## Signal kinds and polarity
| Polarity | Kinds |
|---|---|
| **+ competitor gaining** | rfp_participation, competitor_shortlisted, pricing_undercut, competitor_exec_meeting, competitor_pilot, competitor_hire_into_account, champion_weakening, competitor_reference, competitor_contract_award, competitor_mention |
| **− counter-evidence** | competitor_delivery_issue, competitor_exit, our_win_against, customer_positive_on_us, competitor_price_rise |

Families: `displacement_risk` · `competitive_pursuit` (a contested deal) · `displacement_opportunity` (we can displace them).

## Metrics (deterministic)
- **Velocity:** signals per 30 days over the last 90 days.
- **Momentum:**
  - *accelerating*: 2 or more signals in the last 60 days, and at least 1.5× the prior 60 days;
  - *weakening*: counter-evidence dominates recent signals, recent activity has halved, or there has been no signal for 90 days;
  - *steady*; *resolved*.
- **Confidence:** 0.30 + 0.08 × distinct sources (up to 4) + 0.05 × supporting signals (up to 6) − 0.2 × the counter-evidence share, bounded to 0.1–0.9.
- **Risk:** weighted signal score (High ≥ 7, or ≥ 5 while accelerating).
- **Next event:** a rule table keyed on the last signal kind. It is labelled `PREDICTION` with Low or Medium confidence.

## Evidence requirements
Every signal needs `account_id`, `competitor_id`, and `source`; otherwise it is rejected. Facts and inferences are separated (`verified: false` → INFERENCE). Hypotheses are always labelled.

## Memory behavior
Persists `CompetitiveThread`, `CompetitiveEvent`, `CompetitiveHypothesis`, and `CompetitiveOutcome`, queryable by account, competitor, opportunity, and time.

## Escalation rules
- A High-risk, accelerating thread on a strategic account or a deal of $1M or more → T3 strategy (deal-strategy-agent).
- Contradictory evidence of equal weight → `ESCALATE`.

## Examples
Three signals about Competitor B at BlueWave (an RFP invitation, a pricing undercut, a champion weakening) → **one** thread, accelerating, risk High, predicted next event "commercial pressure / BAFO", with actions to re-thread the champion and prepare a value-based response.

## Failure handling
| Condition | Behaviour |
|---|---|
| Unknown signal kind or missing source | Rejected with a reason |
| Duplicate signal id | Ignored |
| A tenant other than the one bound to the memory file | Refused |

<!-- starter-prompts:start (generated from growth-discovery catalog; do not edit) -->
## Starter prompts
Show these to users in business language; a chosen prompt goes to the Business Orchestrator. Full catalog and context-aware variants: growth-discovery.

**Competitive Threads** (/threads)
- Show me active competitive threads.
- Which competitive threads are accelerating?
- Explain this competitive thread.
- Show me the evidence behind this threat.
- Predict what this competitor could do next.
- What should I do about this threat?
<!-- starter-prompts:end -->
