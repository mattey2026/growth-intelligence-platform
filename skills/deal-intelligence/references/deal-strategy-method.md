# Deal Strategy Method (absorbed from deal-intelligence, retired in v5)

Deciding factors, competitive traps, objection handling, win themes, walk-away test. Competitive inputs now come from competitive-intelligence, and win/loss patterns from win-loss-intelligence.

# Deal Strategy and Competitive Win Plan

Version 3.0 · Domain: Sales · Action classes: Retrieve, Analysis, Recommendation (advice only; no execution)

Stages: Connect → Understand → Analyze → Predict → Recommend → Act → Learn

## Why this skill exists

Generic advice ("build value, multi-thread") does not win deals. Specific moves grounded in this buyer's situation and in what has worked against this competitor in similar deals do. This skill brings together deal evidence, the buying committee, win/loss history, and competitive intelligence to produce a plan the seller can act on this week.

Read `references/enterprise-guardrails.md` and `references/prediction-standards.md` before the first run in a session. Prediction definitions are in `references/prediction-spec.md`.

## Connect (v3.0: application- and data-source-agnostic)

Follow `references/connect-protocol.md`. This skill needs these canonical entities: **opportunity, win/loss records, competitive intelligence**. Typical sources: any CRM, win/loss repository, knowledge base, web. Any of them can supply the data; do not assume a particular vendor. Map vendor fields to the canonical model (`references/semantic-model.md`). For files, run `scripts/data_profiler.py` and `scripts/normalize.py` first. Authorize each source separately, since access to one system never implies access to another. Label outputs **Data → Metric → Insight → Prediction → Recommendation → Action** (guardrails §1), and say which additional source would most improve the answer.
Design standard: `references/skill-design-card.md`. Analytics methods: `references/analytics-methods.md`.

## Inputs
- **Opportunity**: stage, amount, close date, products, and deal history.
- **Evidence**: `deal_risk`, `buying_committee`, and `deal_delta` outputs if available. Otherwise gather the key facts or ask the seller about pain, decision criteria, decision process, and competitors.
- **Competitor(s)**: from the CRM, transcripts, or the user.
- **Win/loss history**: similar closed deals (same segment, product, competitor) with loss reasons and, where available, win/loss interview notes.
- **Competitive intelligence**: internal battlecards and recent public competitor moves (web, cited with date).

## Workflow
1. **Diagnose the situation** in five lines: where the deal truly stands (evidence, not stage), what the buyer is trying to achieve, how they will decide, who decides, and why the deal is stuck.
2. **Identify the core problem.** Pick the one to three things that will decide the outcome. Common patterns: no access to the economic buyer, a weak or unquantified business case, decision criteria shaped by a competitor, no compelling event, procurement or legal as the real bottleneck, or a champion without power.
3. **Look for patterns in similar deals.** What did won deals against this competitor have in common, and how were comparable losses lost? Cite the deals or the number of deals, and note when the sample is small.
4. **Build the competitive position**:
   - Where we are genuinely stronger for **this** buyer's criteria.
   - Where the competitor is genuinely stronger. Be honest here; ignoring it loses deals.
   - Traps to set: questions and proof points that expose the competitor's weakness against this buyer's stated needs.
   - Traps to avoid: arguments the competitor wants us to have.
   - All claims about the competitor must be sourced and current. Unverified claims stay internal and are labelled unverified.
5. **Respond to objections** the buyer actually raised, using their words (with quotes from the evidence). Give a response and a proof point for each.
6. **Define win themes**: two or three themes tied to the buyer's stated outcomes and metrics.
7. **Write the action plan** for the next two weeks: action, owner (account executive, solution engineer, executive sponsor, partner), target stakeholder, date, and what evidence will show that it worked.
8. **Set a walk-away test**: the conditions under which the seller should deprioritize or disqualify the deal. Protecting seller time is part of the strategy.

## Output template

```
DEAL STRATEGY — <Opportunity> · <competitor(s)> · Internal only

SITUATION (Metric / Insight)
...

WHAT WILL DECIDE THIS DEAL
1. ...

COMPETITIVE POSITION
Where we win: ...     Where they win: ...
Set these traps: ...  Avoid these: ...

OBJECTIONS → RESPONSES
| Objection (buyer's words, source) | Response | Proof point |

WIN THEMES
...

14-DAY ACTION PLAN (Recommendation)
| # | Action | Owner | Stakeholder | Date | Success signal |

WALK-AWAY TEST
...

SOURCES AND COVERAGE
```

## Rules
- Every recommendation must connect to a fact about this deal. If a recommendation would apply to any deal, cut it or make it specific.
- Never draft customer-facing statements about competitors that are unsourced or disparaging. That is a legal and reputational risk.
- If the evidence is too thin for a real strategy, say so and list the three facts to get first. This is itself a strategy.
- Confidential win/loss interview content stays internal. Do not quote customers from other deals in material that could reach this buyer.

## Intelligence stages and predictive layer (v2.0)

The workflow above covers **Understand** and much of **Analyze** and **Act**. Add the following:

- **Analyze**: diagnose the deciding factors, using evidence from `deal-intelligence` and `relationship-intelligence`.
- **Predict**: (a) **competitive win rate**: historical win rate against this competitor in this segment and size band, with a Wilson interval and sample size; (b) **similar-deal cohort**: the 20–50 most similar closed deals (segment, size, competitor, stage path, evidence profile), with how the won ones differed from the lost ones; (c) the current win probability from `deal-intelligence`.
- **Recommend**: rank candidate actions by (evidence the action addresses a top risk factor) × (how often won deals in the cohort had it) × (feasibility in 14 days). State plainly that these are associations, not causal effects. For high-stakes moves, suggest a test.
- **Learn**: log the plan and which actions were completed; at deal close, record whether completed actions co-occurred with a win. This feeds the cohort analysis.

Present every prediction as a **prediction card** (`prediction-standards.md` §3), with estimate, band, confidence, method, top factors, and what would change it. Never state a prediction as fact. With thin history, use rules and label them Low confidence. End the run with `prediction_ledger` entries.

## Exceptions
- **Unknown competitor**: build the strategy against "status quo" or "do nothing", and add a discovery question to identify the competitor.
- **Pricing is the core issue**: frame the value case here, and hand the commercial analysis to `pricing-intelligence`.
- **Legal or terms bottleneck**: recommend early Legal engagement; do not draft legal positions.

## Handoff
`{"contract":"win_plan","version":"1.0","opportunity_id":"","deciding_factors":[],"actions":[{"action":"","owner":"","stakeholder":"","due":"","success_signal":""}],"walk_away_conditions":[]}`

## Platform (v4.0)
This skill composes with others per `references/orchestration.md`. It measures its value against a baseline per `references/measurement-framework.md`, and it applies guardrails v4, including §13 prompt-injection protection and §14 tool-use controls.
