# Prediction Spec — daily-growth-briefing

This skill does not create its own models. It surfaces predictions from the source skills (deal slip and win, churn, expansion, forecast range, anomalies), carrying their confidence and drivers forward.

| Element | Signal relevance (ranking) |
|---|---|
| Prediction | Which signals the user will find worth acting on |
| Method | Deterministic score (value × urgency × confidence × novelty × relevance); later tuned from acted-on vs dismissed history (with consent) |
| Accuracy measure | Share of top items acted on; missed-signal audits (outcomes with no prior briefing item) |
| Outcome optimized | Decision latency; risk lead time |
