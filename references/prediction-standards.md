# Prediction Standards (v3.0)

These standards apply to every prediction any skill in this plugin makes. A prediction is a probability-weighted estimate, and it must never be presented as a fact.

## 1. Every skill moves through the same seven stages

| Stage | Question it answers | Output label |
|---|---|---|
| **Connect** | Which authorized sources, mapped to which canonical entities? | Coverage and lineage |
| **Understand** | What is true right now? | Data, Metric |
| **Analyze** | Why is it like this? (descriptive and diagnostic) | Metric, Insight |
| **Predict** | What is likely to happen, how sure are we, and why? | Prediction |
| **Recommend** | What should be done, and what is it expected to change? | Recommendation |
| **Act** | Execute approved actions only | Action |
| **Learn** | Record the prediction and recommendation, then compare with the outcome | Ledger entry |

## 2. Choose the simplest method that works

Use the first method that fits the data you actually have:

| Situation | Method |
|---|---|
| A clear business policy exists (discount bands, notice periods, SLA rules) | **Deterministic rules**. Not a prediction; label it as a rule result |
| Fewer than 200 labelled outcomes, or a new product or segment | **Transparent points-based rules** plus LLM reasoning over evidence. Confidence is always Low |
| 200 or more labelled outcomes with consistent fields | **Logistic regression** for classification (win, slip, churn, conversion) |
| A quantity over time with 8 or more periods of history | **Time-series** approach (seasonal naive, exponential smoothing), always compared against a naive baseline |
| Duration (cycle length, time to close) | **Survival or duration model**, or empirical quantiles by segment |
| Unusual behaviour with no labels | **Anomaly detection**: robust z-scores (median absolute deviation) against the entity's own history and its peer group |
| Unstructured signals (transcripts, email, news) | **LLM extraction into structured features**, which then feed the methods above. The LLM does not produce the probability itself |

Prefer interpretable models. A more complex model is justified only if a backtest shows it materially beats the interpretable one and its explanations remain usable.

## 3. Prediction card (required format)

```
PREDICTION: <what, about which entity>
Horizon: <by date or period>
Estimate: <probability or range>   Historical band: <95% interval of observed rate for similar predictions>
Confidence: High / Medium / Low — <why>
Method: <rules | logistic regression | time-series | anomaly | LLM-evidence>, trained on <n> outcomes, <period>
Top factors: <3–5 factors, each with direction and plain-language meaning>
Assumptions: <e.g., history is representative; no pricing change; independence between deals unless stated>
Limitations: <data gaps, sample size, sources not connected>
What would change it: <evidence that would move the estimate materially>
Not a fact: this is an estimate based on historical patterns.
```

## 4. Confidence methodology

| Label | Requires |
|---|---|
| **High** | Backtest AUC 0.75 or higher (or error at least 20% better than the naive baseline), 50 or more comparable historical cases in the calibration bucket, and complete key inputs |
| **Medium** | AUC 0.65–0.75, 20–49 comparable cases, or 1–2 key inputs missing |
| **Low** | Rules fallback, fewer than 20 comparable cases, AUC below 0.65, significant missing inputs, or the situation differs from history (new product, new market, pricing change) |

Always show the historical band (for example, "deals scored like this closed on time 73–96% of the time") alongside the point estimate.

## 5. Explainability
- Show the 3–5 strongest factors for each individual prediction, with their direction.
- Translate model factors into business language: "close date pushed three times", not `close_date_pushes=3`.
- Separate factors the seller can influence (engage the economic buyer) from factors they cannot (deal size).
- State the counterfactual: which change in evidence would most move the prediction.

## 6. Recommendations
- Tie every recommended intervention to a named factor.
- Do not claim causal uplift ("doing X raises win rate 20%") from observational correlations. Say "deals where X happened won more often", and call for an experiment where the decision matters.

## 7. Accuracy measurement
- **Before use**: a time-based backtest (train on older, test on newer, with no data leakage between deals). Report AUC, Brier score against a base-rate baseline, calibration table, and the share of positive outcomes captured in the top 20% of scores. Compare with the incumbent method (seller commit, CRM probability, or the existing health score).
- **In production**: monthly calibration check, rolling AUC, and a drift check on the distribution of input features.
- **Retrain or recalibrate** when AUC falls by 0.05 or more, when calibration error in any bucket exceeds 10 points, or after a process change such as new stages or pricing.

## 8. Fairness and misuse
- Predict outcomes for deals, accounts, and leads. Never score individual sellers' competence or customers' personal traits.
- Exclude protected attributes and obvious proxies.
- Never let predictions automatically change forecast categories, quotas, compensation, territory, or credit decisions.

## 9. Learning ledger

Log every prediction and recommendation so it can be scored when the outcome is known:

```json
{"contract":"prediction_ledger","version":"3.0","skill":"","prediction_id":"","entity_type":"opportunity|account|lead|forecast","entity_id":"","prediction":"","horizon_end":"","estimate":0.0,"band":[0.0,0.0],"confidence":"High|Medium|Low","method":"","model_version":"","sources":[],"assumptions":[],"top_factors":[],"recommendation":"","recommendation_accepted":null,"outcome":null,"outcome_date":null}
```

When the horizon passes, fill in `outcome`, then report accuracy and recommendation acceptance by skill and by model version. Store the ledger in the data platform, or in a CRM custom object if no data platform is available. Only store data the user is permitted to see.
