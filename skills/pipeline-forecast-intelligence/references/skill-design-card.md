# Skill Design Card — pipeline-forecast-intelligence (v4.0, 24-item standard)

| Item | Detail |
|---|---|
| Skill name | pipeline-forecast-intelligence |
| Business problem | Pipeline reports describe but don't predict; forecast risk and what-if are handled in spreadsheets |
| Persona | Managers, RevOps, CRO, Finance |
| Trigger | "Will we hit the number"; forecast call; "what if deal X slips" |
| Inputs | Scope, period, target, opportunities, history |
| Data sources | CRM or forecast tool, warehouse, finance |
| Connectors / tools | pipeline_whatif, forecast_sim, deal_risk_model, ts_forecast, anomaly |
| Context requirements | Quota/target, fiscal periods, stage rates, correlation assumption |
| Analytics | Coverage, quality, aging, velocity, conversion, leakage, concentration, rep exposure |
| Predictive | P10/P50/P90; probability of hitting target; forecast error; deal-level scenarios |
| Reasoning | Which deals drive the variance; which assumptions matter |
| Decision logic | Go-live bar; scenario deltas; swing-deal ranking |
| Recommendations | Inspect swing deals; pipeline actions; resource moves |
| Actions | None (never submits a forecast); tasks on request |
| Approval | Any published number |
| Output | Pipeline health, forecast range, what-if table, call agenda |
| Evidence | Deal-level inputs and sources |
| Confidence | Model and sample based; scenarios labelled illustrative |
| Error handling | Thin history → wider ranges; missing probabilities → stage rates, disclosed |
| Security | Confidential (MNPI) marking |
| Auditability | Ledger of ranges |
| Baseline | Historical forecast error by week of quarter |
| Success metrics | Error at weeks 4/8/12 vs baseline; P10–P90 hit rate |
| Test scenarios | Deal A slips / B lost / rep unavailable; new product |
| Failure modes | False precision; correlated misses |
