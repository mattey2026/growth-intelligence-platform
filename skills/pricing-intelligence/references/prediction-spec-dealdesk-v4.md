# Prediction Spec — pricing-intelligence

Follow `prediction-standards.md` for confidence, explainability, and the ledger.


## Approved without rework

| Element | Detail |
|---|---|
| Prediction | Approved without rework |
| Historical data | Past submissions with outcomes |
| Real-time data | Current quote and terms |
| Signals | Discount percentile, margin gap, non-standard term count, justification completeness |
| Horizon | Approval decision |
| Confidence | Per standards §4 |
| Explainability | Top factors |
| Intervention | Fix before submitting |
| Outcome optimized | Faster quote-to-close |
| Accuracy measure | AUC; rework rate before and after |

## Approval cycle time

| Element | Detail |
|---|---|
| Prediction | Approval cycle time |
| Historical data | Approval timestamps by path |
| Real-time data | Predicted path |
| Signals | Path, quarter timing, approver load |
| Horizon | Approval |
| Confidence | Medium |
| Explainability | Median and 80th percentile by path |
| Intervention | Submit earlier or pre-brief the approver |
| Outcome optimized | Cycle time |
| Accuracy measure | Predicted vs actual days |
