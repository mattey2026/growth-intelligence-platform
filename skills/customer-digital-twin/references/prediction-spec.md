# Prediction Spec — customer-digital-twin

This skill orchestrates predictions made by other skills. It adds a revenue outlook and combines confidence across sources.

| Element | Account revenue outlook | Cross-source confidence |
|---|---|---|
| Prediction | Revenue next 2–4 quarters (P10/P50/P90) | Reliability of the combined view |
| Historical data | 8 or more quarters of invoiced revenue | — |
| Real-time data | Open orders, pipeline, renewal dates | Source freshness, match rates |
| Signals | Trend, seasonality, contract schedule | Sources present or absent, staleness, match % |
| Horizon | 2–4 quarters | Now |
| Confidence | Backtest vs naive; capped at Medium if usage or service sources are missing | Rule-based |
| Explainability | Components plus contracted vs uncontracted split | Coverage table |
| Intervention | Expansion or renewal timing | Connect missing sources |
| Outcome optimized | Account growth, retention | Decision quality |
| Accuracy measure | Actual vs band | — |
