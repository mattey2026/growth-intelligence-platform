# Prediction Spec — scenario-planner

Scenarios are **not predictions** unless they are grounded in historical frequency.

| Element | Scenario likelihood (optional) |
|---|---|
| Prediction | How often historically drivers were at or below or above the scenario values |
| Historical data | 8 or more quarters of driver values (win rate, pipeline per rep, slip, average deal size) |
| Real-time data | Current quarter's drivers to date |
| Signals | Driver distributions |
| Horizon | Planning period |
| Confidence | Low with fewer than 8 quarters, or when drivers are dependent on each other |
| Explainability | Historical frequency table |
| Intervention | Contingency plans for the most sensitive drivers |
| Outcome optimized | Plan realism; target attainment |
| Accuracy measure | Actual drivers vs assumed; which assumption was most wrong |
