# 7. Adaptive KPIs and the Executive Command Center

- **KPI engine:** the framework comes from the profile. It computes only supported KPIs and lists unsupported ones with the input they need.
  - Test v1: 15 supported. NRR, GRR, CAC, coverage, and win rate are unsupported, each with a reason.
  - Test v2: bookings appeared once O009 closed. Win rate **stayed unsupported** (1 won, 0 lost; at least 10 outcomes needed).
- **Command center:** CEO / Investor / Owner tabs; five questions in order; each KPI shows actual, previous, change, forecast, previous forecast, target, and benchmark, with confidence and source. A change ledger since the last review; drivers; labelled predictions; actions with approval flags; unsupported KPIs and stale sources shown.
- **Contextual memory example:** the Q4-26 bookings outlook is $17.1M vs the previous $16.9M (+1.2%). The change is explained: O009 was booked, while the O010 scope cut falls outside Q4.
- **Design checks:** desktop and mobile screenshots reviewed; tab switching tested; font-fallback and "+0.0%" noise bugs found and fixed.
