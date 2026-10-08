# Deal Desk Mode (the v4 deal-desk-precheck workflow, preserved in full)


# Deal Desk Commercial Pre-Check

Version 3.0 · Domain: Sales → Finance · Action classes: Retrieve, Analysis, Recommendation, Action (submission drafts only). **This skill never approves anything.**

Stages: Connect → Understand → Analyze → Predict → Recommend → Act → Learn

## Why this skill exists

Non-standard deals bounce between Sales, Deal Desk, Finance, and Legal because submissions are incomplete or poorly justified. Checking them before submission removes rework cycles and protects margin. The skill is also a control: it makes policy visible to sellers. It must not become a way to game guardrails.

Read `references/enterprise-guardrails.md` and `references/prediction-standards.md` before the first run in a session. Prediction definitions are in `references/prediction-spec.md`. Margin and cost data are sensitive; show them only to users entitled to them.

## Connect (v3.0: application- and data-source-agnostic)

Follow `references/connect-protocol.md`. This skill needs these canonical entities: **quote, price book, policy, cost/margin, contract terms**. Typical sources: any CPQ, ERP, pricing spreadsheets, CLM. Any of them can supply the data; do not assume a particular vendor. Map vendor fields to the canonical model (`references/semantic-model.md`). For files, run `scripts/data_profiler.py` and `scripts/normalize.py` first. Authorize each source separately, since access to one system never implies access to another. Label outputs **Data → Metric → Insight → Prediction → Recommendation → Action** (guardrails §1), and say which additional source would most improve the answer.
Design standard: `references/skill-design-card.md`. Analytics methods: `references/analytics-methods.md`.

## Inputs
- **Quote**: products, quantities, list price, net price, discount by line, term, billing frequency, payment terms, ramp schedules.
- **Pricing policy**: price books, discount bands by product, segment, and term, and the delegation-of-authority (approval) matrix.
- **Cost or margin data** (if entitled): standard cost or margin by product, delivery cost estimates.
- **Comparable deals**: approved deals in the last 12 months in the same segment, product, and size band.
- **Non-standard terms**: redlines, special clauses, SLAs, termination rights, most-favoured-customer clauses, custom payment terms.
- **Deal context**: competitive situation, strategic value, and multi-year commitment, which form the basis of the justification.

## Workflow
1. **Validate the quote.** Check arithmetic, price book alignment, missing mandatory items (support, required dependencies), and date and term consistency. Report errors first.
2. **Check guardrails** for each line and in total: discount against the allowed band, and the effective discount including free months, ramps, credits, and services write-downs. Hidden concessions count.
3. **Analyse margin** (entitled users only): deal margin against the target, the effect of each concession, and the multi-year view.
4. **Benchmark against comparables**: where this deal's effective discount sits among similar approved deals (percentile and sample size). Note when there are fewer than 10 comparables.
5. **Review terms**: classify each non-standard term as standard, approvable by the Deal Desk, or requiring Legal or Finance. Summarize each neutrally. Do not negotiate it.
6. **Predict the approval path** from the delegation matrix: the approvers required, in order, and the typical turnaround if known. State the rule that triggered each approval level.
7. **Recommend**, in this order:
   - Changes that remove approval levels without harming the customer outcome (give/get trades such as a longer term for a larger discount, prepayment, or a case study commitment).
   - Where the justification is weak, what evidence to add.
8. **Draft the justification** (Action, draft): the business case in the format approvers expect, covering the customer, competitive context, strategic value, concessions and what we get in return, margin impact, and risks. Base it on deal facts, never invented urgency.

## Output template

```
DEAL DESK PRE-CHECK — <Opportunity> · <quote id> · Internal – Confidential

READINESS: Ready / Fix before submitting / Needs a structural change

ERRORS TO FIX
• ...

GUARDRAILS (Metric / Insight)
| Line | List | Net | Discount | Allowed band | Status |
Effective total discount: x% (including <concessions>)

MARGIN (entitled users only): deal x% vs target y%

COMPARABLES: this deal is at the Nth percentile of n similar approved deals

NON-STANDARD TERMS
| Term | Classification | Owner |

PREDICTED APPROVAL PATH
<Approver 1> (rule: ...) → <Approver 2> (rule: ...)

RECOMMENDED CHANGES (give/get)
...

JUSTIFICATION DRAFT — not submitted
...
```

## Rules
- Never approve, and never tell a seller that a deal "will definitely be approved". Predictions are estimates.
- Never advise how to split, restructure, or time deals to avoid required approvals. That is control circumvention. If the user asks for this, decline and explain that the approval policy exists for revenue-recognition and margin controls.
- Treat revenue-recognition-sensitive terms (side letters, acceptance clauses, extended payment terms, bundled free services) as mandatory flags to Finance.
- Hide cost and margin fields from users who are not entitled to them, and state that they were hidden.
- Submit to the approval system only as a draft, and only with the user's approval.

## Intelligence stages and predictive layer (v2.0)

The workflow above covers **Understand** and much of **Analyze** and **Act**. Add the following:

- **Analyze**: guardrails, effective discount, margin, and terms (unchanged from v1); diagnose where the concessions come from.
- **Predict**: (a) **approval as submitted**: likelihood that the submission is approved without rework, using past submissions (discount percentile vs comparables, margin gap, number of non-standard terms, completeness of the justification) via `scripts/propensity_model.py`, or rules when history is thin; (b) **approval cycle time**: empirical median and 80th percentile for this approval path; (c) **discount anomaly**: robust percentile or z-score vs comparable approved deals; (d) **win rate by discount band**: descriptive and observational only. Never present this as price elasticity.
- **Recommend**: give/get changes that reduce rework risk and approval levels.
- **Learn**: log predicted versus actual approval outcome and cycle time.

Present every prediction as a **prediction card** (`prediction-standards.md` §3), with estimate, band, confidence, method, top factors, and what would change it. Never state a prediction as fact. With thin history, use rules and label them Low confidence. End the run with `prediction_ledger` entries.

## Exceptions
- **No pricing policy provided**: validate arithmetic and summarize concessions only; state that guardrail checks were not possible.
- **Multi-currency**: use the company's approved rates and state the rate date.
- **Bundles with services**: flag delivery feasibility for Operations review, which composes with Operations skills.

## Handoff
`{"contract":"commercial_check","version":"1.0","opportunity_id":"","quote_id":"","effective_discount_pct":0,"guardrail_breaches":[],"margin_pct":null,"approval_path":[],"legal_finance_flags":[],"readiness":"ready|fix|restructure"}`

## Platform (v4.0)
This skill composes with others per `references/orchestration.md`. It measures its value against a baseline per `references/measurement-framework.md`, and it applies guardrails v4, including §13 prompt-injection protection and §14 tool-use controls.
