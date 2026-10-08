# Skill Design Card — scenario-planner (v3.0)

| # | Standard item | scenario-planner |
|---|---|---|
| 1 | Business problem | Plans rest on hidden, untested assumptions |
| 2 | Target persona | Sales leaders, RevOps, Finance |
| 3 | Data sources (canonical) | Historical drivers, targets |
| 4 | Required tools/plugins | CRM, warehouse, files |
| 5 | Inputs | Period, target, drivers, scenarios |
| 6 | Data preparation | Derive drivers with sample sizes |
| 7 | Business logic | Explicit driver formula |
| 8 | Analytics (descriptive/diagnostic) | Assumption vs history check |
| 9 | Predictive analytics | Historical frequency of scenarios (optional) |
| 10 | Reasoning | Scenarios are not forecasts |
| 11 | Recommendations | Focus on sensitive drivers |
| 12 | Actions | Excel model or summary |
| 13 | Human approval points | Writing plans or quotas to systems |
| 14 | Outputs | Scenario table, tornado |
| 15 | Success metrics | Plan accuracy; decision time |
| 16 | Baseline | Prior plan vs actual drivers |
| 17 | Accuracy requirements | Most-wrong assumption tracked |
| 18 | Security requirements | Confidential planning data |
| 19 | Failure modes | Invented elasticity; unrealistic drivers |
| 20 | Test scenarios | Capacity plan; price increase; no history |

The full test prompts are in `evals/evals.json` in the source repository.
