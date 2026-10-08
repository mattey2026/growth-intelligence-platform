# Deal Risk Method (absorbed from deal-intelligence v3, retired in v5)

Evidence scoring, red-flag rules R1–R9, stagnation detection, and the slip/win model workflow. Used by deal-intelligence (single and batch mode), pipeline-forecast-intelligence, and daily-growth-briefing.

# Deal Risk Intelligence

Version 3.0 · Domain: Sales · Stages: Connect → Understand → Analyze → Predict → Recommend → Act (approval-gated) → Learn

Replaces `deal-evidence-auditor` (v1). Its evidence scoring is retained here as the diagnostic layer.

## Why this skill exists

CRM fields record what the seller believes. Deals slip because of what the buyer is, or is not, doing. This skill:
1. Measures buyer evidence against what the CRM claims.
2. Predicts slip and loss probability with a model backtested on the company's own history.
3. Tells the seller or manager the one or two interventions most likely to matter for each deal.

It scores **deals**, never sellers.

Read `references/enterprise-guardrails.md` and `references/prediction-standards.md` before the first run in a session. Use `deal_delta` records when available (`references/deal-delta-contract.md`). Prediction definitions are in `references/prediction-spec.md`.

## Connect (v3.0: application- and data-source-agnostic)

Follow `references/connect-protocol.md`. This skill needs these canonical entities: **opportunity (with snapshot or field history), activity, contact, document**. Typical sources: any CRM (Salesforce, Dynamics, HubSpot, SAP Sales Cloud, Oracle CX), pipeline spreadsheets, warehouse snapshot tables, email/calendar, transcript tools, document stores. Any of them can supply the data; do not assume a particular vendor. Map vendor fields to the canonical model (`references/semantic-model.md`). For files, run `scripts/data_profiler.py` and `scripts/normalize.py` first. Authorize each source separately, since access to one system never implies access to another. Label outputs **Data → Metric → Insight → Prediction → Recommendation → Action** (guardrails §1), and say which additional source would most improve the answer.
Design standard: `references/skill-design-card.md`. Analytics methods: `references/analytics-methods.md`.

## Inputs
- **Scope**: one opportunity, a list, or a filter (owner, team, forecast category, close period). Default: the user's own open deals closing this quarter. Only use records within the user's visibility.
- **History**: an opportunity snapshot or field-history export for the last 6–8 quarters (see the CSV schema in `scripts/deal_risk_model.py`). Required for the model. Without it, run in rules mode.
- **Evidence**: email and calendar metadata, transcripts or `deal_delta` records, and documents (proposal, mutual action plan, order form, security review).
- **Framework**: MEDDPICC by default.

## Workflow

### 1. Understand (Data)
For each deal, pull the claimed state (stage, amount, close date, forecast category, next step, qualification fields) and field history (close-date pushes, amount changes, time in stage). Build a buyer-activity timeline, keeping buyer-initiated and seller-initiated activity separate.

### 2. Analyze (descriptive and diagnostic)
- **Evidence scores** per MEDDPICC element, where 3 is Strong (buyer said or did it, specific, within 30 days, from someone with authority), 2 is Partial, 1 is Weak (seller assertion only), 0 is None, and ? is Unknown because the source was not accessible. Unknown is not zero.
- **Red-flag rules** (defaults; replace with the company's values):
  - R1: close within 30 days and paper process scored 0–1.
  - R2: proposal stage or later with no economic buyer interaction in 60 days.
  - R3: two or more close-date pushes.
  - R4: no buyer-initiated activity in 21 days.
  - R5: amount changed more than 20% with no documented reason.
  - R6: single-threaded on a large deal.
  - R7: champion silent 30 days or has left.
  - R8: next step stale more than 14 days.
  - R9: buyer activity in the last 30 days less than half the prior 30.
- **Stagnation**: days in the current stage compared with the historical median for that stage and segment. Flag above the 75th percentile.
- **Diagnosis**: in one or two sentences, why this deal is in this state, citing evidence.

### 3. Predict (Prediction)
Run the model on the history export:
```bash
python scripts/deal_risk_model.py backtest history.csv --target slip   # once per period, or when data changes
python scripts/deal_risk_model.py score history.csv --target slip --out slip.json
python scripts/deal_risk_model.py score history.csv --target win  --out win.json
```
- **Slip**: probability the deal does not close-won by its current close date. Horizon: the current close date.
- **Win**: probability the deal is eventually won. Horizon: end of the next quarter.
- Add evidence features extracted from transcripts and email (economic buyer engaged, paper process started, number of engaged contacts, days since buyer activity) as columns before scoring. The LLM extracts facts; the model estimates probability.
- Present each prediction using the prediction card in `prediction-standards.md` §3: estimate, historical band, confidence, method, top factors, and what would change the estimate.
- If the backtest AUC is below 0.65, or there are fewer than 200 labelled rows, the script falls back to rules. Report risk as High, Medium, or Low with Low confidence, and say that history was too thin for a model.
- **Revenue at risk** = the sum of amount × slip probability across the scope. Show it with the band.

### 4. Recommend (Recommendation)
For each deal, connect the top factors the seller can influence to an intervention:

| Top factor | Intervention |
|---|---|
| Economic buyer not engaged | Executive-to-executive meeting request via the champion, within 7 days |
| No paper process / close date within 30 days | Map procurement steps with the buyer; propose a mutual action plan |
| Buyer silent 21 days or more | Multi-channel re-engagement through a second contact; offer to check the timeline |
| Close date pushed 2 or more times | Reset the close date to the evidenced date; move the forecast category (proposal) |
| Single-threaded | Hand off to `relationship-intelligence` for a multi-threading plan |
| Competitor present plus weak criteria | Hand off to `deal-intelligence` |

Prioritize deals by revenue at risk multiplied by how actionable the risk is, not by probability alone. Do not claim that an intervention will raise probability by a specific amount (see standards §6).

### 5. Act (approval-gated)
You may propose close-date or forecast-category changes and tasks for the recommended interventions. Present them as a change set; the seller approves each field individually. Never apply them automatically. Managers cannot approve changes to another seller's records through this skill.

### 6. Learn
Write `prediction_ledger` entries for every slip and win prediction and every recommendation (standards §9). When `outcome` is available for past entries, report the last period's calibration: "Of the deals we rated 60–80% likely to slip, 71% slipped."

## Output template

```
DEAL RISK INTELLIGENCE — <scope> · <date> · Confidential – internal only
Model: <method>, backtest AUC <x> vs seller-commit baseline <y>, trained on <n> deals (<period>)

SUMMARY
Open $X · Predicted revenue at risk $R (band $a–$b) · Deals needing action: n

PRIORITY DEALS (highest revenue at risk first)
| Deal | Amount | Close | Category | Slip probability (band, confidence) | Win probability | Top factors | Recommended action |

DEAL CARDS
<Deal> — Claimed vs evidenced · MEDDPICC scores · Red flags · Diagnosis
Prediction card(s) · Recommended intervention · Proposed changes (pending approval)

ACCURACY OF PAST PREDICTIONS (when the ledger has outcomes)
COVERAGE / DATA LIMITS
LEDGER ENTRIES (JSON)
```

## Exceptions
- **No history export**: evidence scoring plus rules-based risk only; Low confidence throughout; list the history fields needed.
- **Missing evidence sources**: mark elements "?", and never treat a missing channel (phone, in-person) as negative evidence.
- **Deal very different from history** (new product, much larger than past deals): cap confidence at Low and say why.
- **Model contradicts strong evidence** (for example, predicts a high slip probability but a signed order form is in legal review): show both views, and let the evidence win in the recommendation.
- **User asks for a seller ranking**: decline, and offer a deal-level view instead.

## Handoff
`{"contract":"deal_risk","version":"2.0","opportunities":[{"opportunity_id":"","slip_probability":0,"slip_band":[0,0],"win_probability":0,"confidence":"","top_factors":[],"element_scores":{},"red_flags":[],"recommended_action":""}],"revenue_at_risk":0,"model":{"method":"","auc":0,"trained_on":0}}`

Consumers: `pipeline-forecast-intelligence`, `deal-intelligence`, `relationship-intelligence`.

## Quality bar
- Every prediction has a band, a confidence level, and its factors.
- Every recommendation is tied to a factor.
- Backtest results are shown before users are asked to rely on the model.
- No automatic changes are ever made to records.

## Platform (v4.0)
This skill composes with others per `references/orchestration.md`. It measures its value against a baseline per `references/measurement-framework.md`, and it applies guardrails v4, including §13 prompt-injection protection and §14 tool-use controls.
