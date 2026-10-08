# Prediction Spec — meeting-follow-through

Follow `prediction-standards.md` for confidence, explainability, and the ledger.


## Buyer commitment missed

| Element | Detail |
|---|---|
| Prediction | Buyer commitment missed |
| Historical data | Past commitments with met or missed outcomes (built by this skill over time) |
| Real-time data | Commitment wording, owner, due date, attendees |
| Signals | Specific owner, explicit date, owner present, account track record |
| Horizon | Due date |
| Confidence | Low until 200 or more labelled commitments exist, then model-based |
| Explainability | Factors listed per commitment |
| Intervention | Proactive reminder; secure a second owner |
| Outcome optimized | On-time mutual action plan execution |
| Accuracy measure | Precision and recall of risk flags vs actual misses |

## Momentum shift

| Element | Detail |
|---|---|
| Prediction | Momentum shift |
| Historical data | Prior deal_delta records for the deal |
| Real-time data | This meeting's extraction |
| Signals | Buyer question count, timeline specificity, new stakeholders, sentiment of objections |
| Horizon | Next 30 days |
| Confidence | Low or Medium |
| Explainability | Comparison table vs the prior meeting |
| Intervention | Escalate or re-plan |
| Outcome optimized | Earlier risk detection |
| Accuracy measure | Correlation of momentum drops with later slip |
