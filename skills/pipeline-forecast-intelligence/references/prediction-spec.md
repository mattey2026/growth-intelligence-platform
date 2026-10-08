# Prediction Spec — pipeline-forecast-intelligence

Follow `prediction-standards.md` for confidence, explainability, and the ledger.


## Period-end bookings (P10/P50/P90)

| Element | Detail |
|---|---|
| Prediction | Period-end bookings (P10/P50/P90) |
| Historical data | 6–8 quarters of weekly snapshots and outcomes; forecast submissions |
| Real-time data | Current deal probabilities (deal_risk), closed to date |
| Signals | Deal probabilities, amounts, correlation assumption, historical error |
| Horizon | Quarter end |
| Confidence | High when deal models are High confidence and 6 or more quarters of history exist |
| Explainability | Swing deals and their variance share |
| Intervention | Inspect swing deals; reallocate resources |
| Outcome optimized | Forecast accuracy |
| Accuracy measure | Did the actual fall inside P10–P90? Mean absolute percentage error by week vs the submitted forecast |

## Pipeline coverage risk

| Element | Detail |
|---|---|
| Prediction | Pipeline coverage risk |
| Historical data | Stage-to-close conversion by segment, 4 or more quarters |
| Real-time data | Next quarter's pipeline |
| Signals | Coverage ratio, stage mix, pipeline age |
| Horizon | Next quarter |
| Confidence | Medium |
| Explainability | Coverage vs the required ratio |
| Intervention | Pipeline generation actions |
| Outcome optimized | Next-quarter attainment |
| Accuracy measure | Predicted vs actual next-quarter bookings |
