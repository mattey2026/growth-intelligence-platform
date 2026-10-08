# Skill Design Card — business-watch (v5.0, 24-item standard)

| Item | Detail |
|---|---|
| Skill name | business-watch |
| Business problem | Leaders can't watch every system |
| Persona | Executives, managers, CS leaders |
| Trigger | 'Alert me when…' |
| Inputs | Watch definitions; state |
| Data sources | Twin, forecast, deal contracts |
| Connectors / tools | watch_evaluator |
| Context requirements | Thresholds; owners |
| Analytics | Condition evaluation |
| Predictive | Impact via investigation skills |
| Reasoning | Investigate before notifying |
| Decision logic | Severity; false-fire tuning |
| Recommendations | Next action per fired watch |
| Actions | Owner-approved channels |
| Approval | Saving watches; channels; remediation |
| Output | Watch results |
| Evidence | Previous → current values |
| Confidence | From the investigating skill |
| Error handling | Misconfigured → reported |
| Security | Owner-scoped |
| Auditability | watch_results |
| Baseline | Time from condition to action |
| Success metrics | −80% latency; <10% false fires |
| Test scenarios | $6M slip fires, $1M doesn't; typo metric |
| Failure modes | Alert fatigue |
