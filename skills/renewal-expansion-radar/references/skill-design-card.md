# Skill Design Card — renewal-expansion-radar (v3.0)

| # | Standard item | renewal-expansion-radar |
|---|---|---|
| 1 | Business problem | Churn is detected too late |
| 2 | Target persona | AMs, CSMs, renewal managers |
| 3 | Data sources (canonical) | Contracts, usage, cases, AR, surveys |
| 4 | Required tools/plugins | CRM/CLM, analytics, ITSM, ERP |
| 5 | Inputs | Book of accounts, horizon |
| 6 | Data preparation | Account identity joins |
| 7 | Business logic | Signal thresholds; notice deadlines |
| 8 | Analytics (descriptive/diagnostic) | Signal table, drivers |
| 9 | Predictive analytics | Churn/downsell and expansion propensity; anomalies |
| 10 | Reasoning | Drivers explain every rating |
| 11 | Recommendations | Save, stabilize, or expand plays |
| 12 | Actions | Tasks |
| 13 | Human approval points | Customer contact; offers |
| 14 | Outputs | Radar table, account detail |
| 15 | Success metrics | Gross and net revenue retention; lead time |
| 16 | Baseline | Historical churn and flag timing |
| 17 | Accuracy requirements | Churned value captured in top decile |
| 18 | Security requirements | Finance data entitlement |
| 19 | Failure modes | Poor joins; false alarms |
| 20 | Test scenarios | Book review; critical account |

The full test prompts are in `evals/evals.json` in the source repository.
