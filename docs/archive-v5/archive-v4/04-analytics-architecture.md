# 4. Analytics Architecture

Every relevant skill moves through **Descriptive → Diagnostic → Predictive → Prescriptive → Action**, and every metric supports **Metric → Explanation → Drivers → Prediction → Recommended Action**.

| Layer | Question | Methods (deterministic first) | Engine |
|---|---|---|---|
| Descriptive | What happened? What is happening? What changed? | Aggregation with formulas, trends, segmentation, funnel, cohort | pandas; `data_profiler`, `pipeline_whatif` (descriptive) |
| Diagnostic | Why? What drives it? | Variance bridges, driver decomposition, Spearman correlation with sample size, cohort comparison, anomaly drill-down | pandas; `anomaly_detect` |
| Predictive | What is likely? | Logistic propensity (win, slip, churn, expansion, conversion); time series (Holt-Winters vs naive); Monte Carlo (forecast, what-if); empirical quantiles (cycle time); robust z-scores (anomalies) | `deal_risk_model`, `propensity_model`, `ts_forecast`, `forecast_sim`, `pipeline_whatif`, `anomaly_detect` |
| Prescriptive | What should we do? | Factor-to-action rules; cohort-associational next-best-action; value × urgency × feasibility ranking; whitespace expected value; multi-criteria allocation | Skill logic; `whitespace_matrix`, `account_prioritizer`, `signal_ranker` |
| Scenario | What if? | Driver models, tornado sensitivity, deal-level overrides | `scenario_model`, `pipeline_whatif` |
| Action | What can we execute? | Change sets, approvals, audit | Connectors + guardrails §5 |

**Division of labour.** Code computes. Claude interprets, contextualizes, explains, and turns the result into action. The LLM extracts features from unstructured text (transcripts, email, documents) but never produces a probability by itself.
