# 15–16. Analytics and Predictive Intelligence Architecture

Every relevant skill moves through **Descriptive → Diagnostic → Predictive → Prescriptive**. Code computes; Claude interprets and turns the result into action.

| Capability | Method | Engine |
|---|---|---|
| KPI, trend, segmentation, cohort, funnel | Deterministic aggregation with formulas | pandas, data-intelligence |
| Variance, driver, root cause | Driver tree, price/volume bridge, recursive drill-down | `driver_tree.py` |
| Correlation | Spearman with n; two-proportion tests; "association" labels | `winloss_analyzer.py` |
| Classification and propensity | L2 logistic regression, time-based backtest, rules fallback | `deal_risk_model.py`, `propensity_model.py` |
| Regression and elasticity | Logistic with controls; confounding detection → assumption ranges | `pricing_model.py` |
| Time series and forecasting | Naive, seasonal naive, Holt-Winters, selected by backtest | `ts_forecast.py` |
| Probabilistic forecast and what-if | Correlated Monte Carlo, common random numbers | `forecast_sim.py`, `pipeline_whatif.py` |
| Risk scoring | Explained rule composites (9 dimensions), pattern strength | account strategist, `signal_correlator.py` |
| Anomaly detection | Robust z (self and peer); competitor presence shifts | `anomaly_detect.py`, `competitive_watch.py` |
| Scenario modelling | Driver models, tornado | `scenario_model.py` |
| Optimization | Priority and allocation under constraints (EV × timing × fit); NBA weights with rank stability | `opportunity_scorer.py`, `account_prioritizer.py` |

## Predictive architecture
| Element | Design |
|---|---|
| Lifecycle | Define → data audit → incumbent baseline → time-based backtest → go/no-go → score → explain → ledger → monitor → recalibrate |
| Go-live bar | AUC ≥ 0.70 and better than the incumbent method; calibration within 10 points per bucket; ranges hit at least 80% of the time |
| Every prediction shows | Horizon, estimate and band, confidence, method and model version, drivers, evidence, assumptions, limitations; never presented as fact |
| Learning inputs | Win/loss reliable features; ledger outcomes; orchestrator pattern precision |
| Causality | Associations only, unless there is an experiment. Pricing detects confounding explicitly |
| Monitoring | Monthly AUC and MAPE, calibration, feature drift, recommendation acceptance and outcomes (guardrails §15) |
