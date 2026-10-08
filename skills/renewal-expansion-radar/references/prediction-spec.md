# Prediction Spec — renewal-expansion-radar

Follow `prediction-standards.md` for confidence, explainability, and the ledger.


## Churn or downsell at renewal

| Element | Detail |
|---|---|
| Prediction | Churn or downsell at renewal |
| Historical data | Past renewals (2+ years) with outcomes and signal snapshots |
| Real-time data | Usage, cases, AR, NPS, sponsor status |
| Signals | Utilization trend, case trend, severity 1–2, escalations, days overdue, NPS, sponsor change, uplift, tenure |
| Horizon | Renewal date (flagged 6–9 months ahead) |
| Confidence | Per standards §4 |
| Explainability | Top factors per account |
| Intervention | Save or stabilize play |
| Outcome optimized | Gross revenue retention |
| Accuracy measure | AUC; share of churned value in the top risk decile; average lead time |

## Expansion within 12 months

| Element | Detail |
|---|---|
| Prediction | Expansion within 12 months |
| Historical data | Past expansions |
| Real-time data | Usage and adoption, org signals |
| Signals | Utilization above 90%, adjacent adoption, new business units, peer whitespace |
| Horizon | 12 months |
| Confidence | Per standards §4 |
| Explainability | Top factors |
| Intervention | Expansion play |
| Outcome optimized | Net revenue retention |
| Accuracy measure | AUC; expansion rate by decile |

## Usage or case anomaly

| Element | Detail |
|---|---|
| Prediction | Usage or case anomaly |
| Historical data | 12+ weeks of metrics |
| Real-time data | Latest week |
| Signals | Robust z-score self and peer |
| Horizon | Now |
| Confidence | Medium to High |
| Explainability | Deviation |
| Intervention | Early outreach |
| Outcome optimized | Earlier intervention |
| Accuracy measure | Precision of alerts |
