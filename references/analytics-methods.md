# Embedded Analytics Methods (v3.0)

Analytics is built into every skill, not added as a separate reporting layer. **Choose the right method for the question.** Use deterministic calculation wherever it is sufficient. Use Claude to interpret, contextualize, explain, and turn results into action, never to replace arithmetic or statistics. Run calculations in code (the bundled scripts or Python) rather than doing mental arithmetic.

| Type | Capability | Default method | Tool |
|---|---|---|---|
| **Descriptive** | KPIs, trends, historical performance | Deterministic aggregation with formulas shown; period-over-period change | Python / pandas |
| | Segmentation | Group-by across canonical dimensions; Pareto (80/20) analysis | pandas |
| | Pipeline, customer, and revenue analysis | Stage funnel, coverage, velocity (count × win rate × average deal ÷ cycle length), cohort analysis | pandas |
| **Diagnostic** | Variance analysis | Plan vs actual vs prior; price, volume, and mix decomposition | pandas |
| | Driver and performance decomposition | Additive bridge (waterfall); contribution by segment | pandas |
| | Correlation analysis | Spearman correlation with sample size; always add "correlation ≠ causation" | pandas |
| | Root cause | Drill-down to the segment that explains most of the variance, then Claude reasons over the evidence | pandas + LLM |
| | Anomaly investigation | Robust z-score (self and peer), then drill-down | `anomaly_detect.py` |
| **Predictive** | Win probability, slippage | Logistic regression, backtested | `deal_risk_model.py` |
| | Churn, expansion, lead conversion, customer growth | Propensity model | `propensity_model.py` |
| | Revenue or bookings forecast (period totals) | Seasonal naive or Holt-Winters, compared with a naive baseline | `ts_forecast.py` |
| | Forecast from open pipeline | Monte Carlo over deal probabilities | `forecast_sim.py` |
| | Time to close | Empirical quantiles by segment and stage (survival-style) | pandas |
| | Revenue at risk, pipeline risk | Sum of value × probability, with a band | scripts above |
| **Prescriptive** | Next-best-action, interventions | Factor-to-action rules plus similar-deal cohort (associational) | skill logic |
| | Resource allocation | Rank by value at risk × actionability, within capacity | pandas + LLM |
| **Scenario** | Revenue, pipeline, forecast, pricing, capacity; best, base, and worst case | Driver-based model with explicit assumptions and sensitivity (tornado) | `scenario_model.py` |

## Rules
- Show formulas for metrics, and the assumptions for every scenario and prediction.
- State the sample size behind every rate. Merge segments that have fewer than 20 records.
- Never extrapolate a trend from fewer than 8 periods without a warning. With fewer than 4 periods, do not forecast at all; describe the data only.
- Pricing scenarios need a stated elasticity assumption. If no elasticity has been measured, show a range of assumptions rather than a single number.
