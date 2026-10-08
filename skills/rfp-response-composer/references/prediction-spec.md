# Prediction Spec — rfp-response-composer

Follow `prediction-standards.md` for confidence, explainability, and the ledger.


## Bid win probability

| Element | Detail |
|---|---|
| Prediction | Bid win probability |
| Historical data | Past RFPs with outcome and attributes |
| Real-time data | Current RFP analysis, relationship data |
| Signals | Pre-RFP engagement, requirements shaped, incumbent, compliance %, competitors, size |
| Horizon | Award date |
| Confidence | Usually Low or Medium (small samples) |
| Explainability | Scorecard plus historical rates by factor |
| Intervention | Bid / no-bid / conditional |
| Outcome optimized | Win rate per bid hour |
| Accuracy measure | Calibration across bids; win rate of 'bid' decisions |

## Response effort (hours)

| Element | Detail |
|---|---|
| Prediction | Response effort (hours) |
| Historical data | Logged hours on past bids |
| Real-time data | Question and gap counts |
| Signals | Questions, Needs-expert count, sections, format complexity |
| Horizon | Submission |
| Confidence | Medium when 10 or more past bids exist |
| Explainability | Comparable bids |
| Intervention | Staffing plan |
| Outcome optimized | On-time, lower-cost responses |
| Accuracy measure | Predicted vs actual hours |
