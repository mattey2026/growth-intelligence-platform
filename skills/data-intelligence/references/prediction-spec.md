# Prediction Spec — data-intelligence

| Element | Period forecast (bookings, revenue, pipeline creation) | Anomaly detection |
|---|---|---|
| Prediction | Next 1–6 period totals, with an 80% interval | Metric values abnormal vs own history or peers |
| Historical data | 8 or more periods (24 or more for seasonality) | 6 or more periods per entity |
| Real-time data | Latest period | Latest period |
| Signals | Level, trend, seasonality | Robust z-scores |
| Horizon | 1–6 periods | Now |
| Confidence | Backtest MAPE vs naive; Low with fewer than 8 periods | High with 12 or more periods and a stable baseline |
| Explainability | Method, components, backtest table | Baseline median, deviation |
| Intervention | Adjust the plan or pipeline generation | Investigate the entity or segment |
| Outcome optimized | Planning accuracy | Earlier issue detection |
| Accuracy measure | Actual vs P10–P90; MAPE vs naive | Precision of flags |
