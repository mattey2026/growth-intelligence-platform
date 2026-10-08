# Skill Design Card — business-intelligence-copilot (v5.0, 24-item standard)

| Item | Detail |
|---|---|
| Skill name | business-intelligence-copilot |
| Business problem | 'Why' questions take analysts days |
| Persona | Executives, managers, RevOps, Finance |
| Trigger | 'Why is X behind', 'what's driving' |
| Inputs | Question; data |
| Data sources | Any, via data-intelligence |
| Connectors / tools | driver_tree, pipeline_whatif, winloss, ts_forecast |
| Context requirements | Plan definitions, hierarchy, fiscal calendar |
| Analytics | Variance, driver tree, price/volume bridge, cross-function tests |
| Predictive | Trajectory P10–P90 |
| Reasoning | Test layered drivers; report unexplained remainder |
| Decision logic | Stop when the gap is explained; quantify contributions |
| Recommendations | 3–5 actions on controllable drivers |
| Actions | Hand to owning skills |
| Approval | Via the owning skills |
| Output | BI answer |
| Evidence | Arithmetic shown; sources |
| Confidence | Per driver |
| Error handling | Blocked function → layer marked untested |
| Security | Scoped to entitlement |
| Auditability | bi_answer contract |
| Baseline | Analyst hours per question; decision latency |
| Success metrics | ≥ 90% audited-correct answers; −80% time |
| Test scenarios | APAC gap; ambiguous plan; blocked finance |
| Failure modes | Parts not adding up; causal overreach |
