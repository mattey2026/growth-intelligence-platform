# Prediction Spec — meeting-intelligence-brief

Follow `prediction-standards.md` for confidence, explainability, and the ledger.


## Account anomaly (early warning)

| Element | Detail |
|---|---|
| Prediction | Account anomaly (early warning) |
| Historical data | 12+ weeks of account metrics (cases, usage, email or meeting volume) |
| Real-time data | Latest week |
| Signals | Robust z-score vs the account's own history and vs peers |
| Horizon | Now |
| Confidence | High when there are 12 or more periods and a stable baseline; Low when fewer than 6 |
| Explainability | Metric, baseline median, deviation |
| Intervention | Raise it in the meeting, or prepare a recovery answer |
| Outcome optimized | No surprises in meetings; retained trust |
| Accuracy measure | Share of flags confirmed as real issues (precision) |

## Likely buyer topics

| Element | Detail |
|---|---|
| Prediction | Likely buyer topics |
| Historical data | Past meeting topics per stakeholder (from deal_delta) |
| Real-time data | Open cases, recent threads, news |
| Signals | Unresolved issues, recent asks, role priorities |
| Horizon | This meeting |
| Confidence | Medium or Low (LLM inference) |
| Explainability | Basis for each topic |
| Intervention | Prepare answers and proof points |
| Outcome optimized | Meeting reaches an agreed next step |
| Accuracy measure | Topic hit rate vs the follow-through record |
