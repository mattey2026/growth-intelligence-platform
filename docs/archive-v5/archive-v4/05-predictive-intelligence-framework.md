# 5. Predictive Intelligence Framework

Full standard: `references/prediction-standards.md`.

**Lifecycle:** Define → Data audit → Baseline (incumbent method) → Backtest (time-based, no leakage) → Go/no-go → Score → Explain → Ledger → Monitor (calibration, drift) → Recalibrate.

| Prediction | Method | Minimum data | Go-live bar | Skill |
|---|---|---|---|---|
| Win probability, deal slippage | Logistic regression + rules fallback | 200 labelled deals; 6–8 quarters of snapshots | AUC ≥ 0.70 and better than the seller-commit baseline | deal-risk / deal-intelligence |
| Revenue and bookings forecast | Monte Carlo on deal probabilities; Holt-Winters for totals | Deal probabilities; 8+ periods | Actual inside P10–P90 at least 80% of the time | pipeline-forecast |
| Churn, renewal | Propensity | 200 renewals | AUC ≥ 0.70; captures churned value in top decile | renewal radar / account strategist |
| Expansion, cross-sell, upsell | Propensity per offering; whitespace base rates | 200 outcomes, or peer base rates | Conversion lift by decile | account strategist |
| Lead conversion | Propensity | 200 converted/unconverted leads | Lift vs current routing | lead triage (P1) |
| Revenue at risk, margin at risk | Value × probability, with band | Inputs above; cost data | Reconciles with Finance | several |
| Sales-cycle duration | Empirical quantiles by segment and stage | 30 won deals per cell | Calibration of quantiles | pipeline-forecast |
| Stakeholder risk | Evidence rules → propensity when labelled | Interaction history | Precision of flags | buying-committee |
| Demand and capacity | Time series + driver models | 8+ periods | MAPE better than naive | scenario / capacity (P1) |
| Anomalies | Robust z-score, self and peer | 6–12 periods | Precision of flags | all |

**Always shown** with each prediction: horizon, band, confidence, drivers, evidence, assumptions, limitations. Predictions are never presented as facts.
