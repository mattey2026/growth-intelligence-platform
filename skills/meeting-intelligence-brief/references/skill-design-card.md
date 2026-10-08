# Skill Design Card — meeting-intelligence-brief (v3.0)

| # | Standard item | meeting-intelligence-brief |
|---|---|---|
| 1 | Business problem | Sellers enter meetings without cross-system context |
| 2 | Target persona | AEs, AMs, CSMs, executives |
| 3 | Data sources (canonical) | Calendar, CRM, service, finance, web |
| 4 | Required tools/plugins | Calendar, CRM, service/ITSM, ERP, web |
| 5 | Inputs | Meeting, purpose, audience |
| 6 | Data preparation | Attendee resolution; identity matching |
| 7 | Business logic | Landmine rules; what-changed detection |
| 8 | Analytics (descriptive/diagnostic) | Account snapshot, trends |
| 9 | Predictive analytics | Account anomalies; likely buyer topics |
| 10 | Reasoning | Focus on this meeting's purpose |
| 11 | Recommendations | Objective, agenda, questions |
| 12 | Actions | None (read-only) |
| 13 | Human approval points | Only if shared externally |
| 14 | Outputs | One-page brief |
| 15 | Success metrics | Prep time; next-step rate |
| 16 | Baseline | Time diary; next-step rate |
| 17 | Accuracy requirements | Anomaly precision |
| 18 | Security requirements | Per-system entitlement |
| 19 | Failure modes | Stale data; too long |
| 20 | Test scenarios | CFO meeting; new prospect; shareable version |

The full test prompts are in `evals/evals.json` in the source repository.
