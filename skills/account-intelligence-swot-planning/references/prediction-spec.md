# Prediction Spec — account-intelligence-swot-planning

| Prediction | Method | Historical data | Signals | Horizon | Confidence basis | Intervention | Accuracy measure |
|---|---|---|---|---|---|---|---|
| Renewal / churn | `propensity_model.py` (≥ 200 past renewals) or rules | Past renewals with signal snapshots | Utilization, cases, escalations, DSO, NPS, sponsor change, uplift | Renewal date | Standards §4 | Save or stabilize play | AUC; churned value captured in the top decile |
| Expansion; cross-sell and upsell propensity | `propensity_model.py` per offering | Past expansions by offering | Utilization >90%, adjacent adoption, peer ownership, new business units | 12 months | Standards §4 | Expansion play | AUC; conversion by decile |
| Revenue growth potential | `ts_forecast.py` + whitespace expected value | 8+ quarters of revenue; install base | Trend, seasonality, peer spend | 4 quarters | Backtest vs naive; peer count | Growth plan | Actual vs band |
| Revenue at risk | Renewal value × churn p + Σ(opportunity value × slip p) | As above | As above | Period | Inherited from the inputs | Prioritize saves | Realized loss vs predicted |
| Competitive displacement | Evidence rules | Competitive losses | Competitor mentions, pilot, RFP, price benchmark | 6 months | Low or Medium | Competitive response | Precision of flags |
| Stakeholder attrition | Evidence rules; model if labelled | Departures | Silence, role-change signals, reorganization | 90 days | Low or Medium | Multi-thread | Precision |
| Relationship deterioration | Engagement trend (robust z-score) | 12+ months of interactions | Buyer-initiated activity, meeting declines | 90 days | Medium | Executive re-engagement | Precision |
| Opportunity slippage | Via `deal-intelligence` | Snapshots | Its signals | Close date | Inherited | Deal intervention | Inherited |
| Customer health | Rule composite (`risk-framework.md`) | — | 9 dimensions | Now | Rule-based | Risk plan | Agreement with expert panel |
| Account profitability | Deterministic margin | Cost-to-serve, discounts | Revenue, COGS, service cost | TTM / next year | Data completeness | Commercial actions | Reconciles with Finance |
| Strategic importance | Weighted rubric | — | Size, growth, logo value, reference value | Now | Rubric | Coverage model | Leadership agreement |

Each prediction is presented as a prediction card with evidence, drivers, assumptions, and limitations. None is presented as a fact.
