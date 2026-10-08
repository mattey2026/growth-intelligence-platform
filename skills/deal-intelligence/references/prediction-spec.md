# Prediction Spec — deal-intelligence

| Prediction | Method | Historical data | Signals | Horizon | Confidence | Intervention | Accuracy measure |
|---|---|---|---|---|---|---|---|
| Slip | Logistic regression (deal_risk_model) | 6–8 quarters of snapshots | Pushes, buyer activity, economic buyer, paper process, contacts, days to close, days in stage | Close date | Standards §4 | Close-plan actions | AUC and calibration vs seller commit |
| Win | Same | Same | Same + evidence scores | End of next quarter | Standards §4 | Pursue / qualify out | AUC vs CRM stage probability |
| Remaining cycle time | Empirical quantiles by stage and segment | 30+ comparable won deals per cell | Stage, segment, size | To close | Sample size | Reset the close date | Quantile coverage |
| Close-date feasibility | Remaining steps × historical step durations | Step timestamps | Paper-process steps | Close date | Medium when step history exists | Re-plan | Hit rate |
