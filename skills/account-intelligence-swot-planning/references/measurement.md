# Measurement: Baseline and Targets

## Baseline (current account-planning process)
Measure over 2–4 weeks with 10–20 account managers:

| Measure | Method |
|---|---|
| Account research time | Time diary per account plan, plus observed sessions |
| Plan preparation time | Time from start to approved plan |
| Data sources and screens accessed | Observed count per plan |
| Opportunity identification rate | Opportunities in manual plans that became qualified opportunities within 6 months |
| Risk identification rate | Share of later churn or downsell events flagged in the plan beforehand |
| Stakeholder coverage | Roles covered vs the required roles |
| Evidence coverage | Share of plan statements with a cited source |
| Plan adoption | Plans opened or updated per month |
| Forecast accuracy (account level) | Predicted vs actual revenue or renewal outcome |

## Targets

| Target | Measure |
|---|---|
| ≥ 70% reduction | Research effort |
| ≥ 50% reduction | Plan-preparation time |
| ≥ 90% | Evidence coverage for material recommendations (reported automatically in every output) |
| ≥ 90% accuracy | Defined classification and risk-detection cases (e.g., risk level vs expert panel, contract-expiry detection, sponsor departure), on a labelled test set of 100 or more cases |
| Measurable uplift | Whitespace identified and converted, expansion pipeline, revenue influenced, net revenue retention, renewal and churn outcomes (matched control group) |

## Accuracy protocol
- **Classification and risk-detection**: an expert panel labels a blind sample, and precision, recall, and accuracy are computed per risk dimension.
- **Predictions**: ledger-based AUC and calibration (`prediction-standards.md` §7).
- **Outcome attribution**: compare pilot accounts with matched control accounts. Claim only the difference against control.
