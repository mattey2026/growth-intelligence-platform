# Prediction Spec — relationship-intelligence

Follow `prediction-standards.md` for confidence, explainability, and the ledger.


## Stakeholder disengagement (30d)

| Element | Detail |
|---|---|
| Prediction | Stakeholder disengagement (30d) |
| Historical data | Interaction history per contact with later silence labels |
| Real-time data | Last 60 days of meetings, emails, response times |
| Signals | Interaction trend, response latency, declines, cc-only drift |
| Horizon | 30 days |
| Confidence | Low to Medium |
| Explainability | Trend chart description plus factors |
| Intervention | Re-engagement through an alternate path |
| Outcome optimized | Avoid single points of failure |
| Accuracy measure | Precision of disengagement flags |

## Coverage-conditional win rate

| Element | Detail |
|---|---|
| Prediction | Coverage-conditional win rate |
| Historical data | Closed deals with role coverage |
| Real-time data | Current coverage |
| Signals | Economic buyer, security, procurement, and executive sponsor present |
| Horizon | Deal close |
| Confidence | Medium, with Wilson interval by sample size |
| Explainability | Win rate by coverage with sample sizes |
| Intervention | Close the highest-lift gap |
| Outcome optimized | Win rate |
| Accuracy measure | Calibration of conditional rates on the next quarter |
