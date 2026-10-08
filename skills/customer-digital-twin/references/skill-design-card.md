# Skill Design Card — customer-digital-twin (v5.0, 24-item standard)

| Item | Detail |
|---|---|
| Skill name | customer-digital-twin |
| Business problem | Account context rebuilt each time; no memory of change |
| Persona | AMs, AEs, CSMs, executives; all account skills |
| Trigger | Account 360, 'what changed and when', refresh schedule |
| Inputs | Account id; sources; prior twin |
| Data sources | CRM, ERP, ITSM, usage, marketing, CLM, web |
| Connectors / tools | entity_resolver, twin_update, anomaly |
| Context requirements | Hierarchy level; refresh cadence; store location |
| Analytics | Trends (slope per 30d), change log, tenure of current state |
| Predictive | From owning skills (churn, expansion, slip) |
| Reasoning | Causes stated as hypotheses; temporal order is not cause |
| Decision logic | System of record wins; append-only; confidence by snapshot count |
| Recommendations | 3–5 actions linked to changes |
| Actions | Snapshot write; hand-offs |
| Approval | First store configuration; all hand-off actions |
| Output | Twin view |
| Evidence | Lineage per fact |
| Confidence | Per trend and prediction |
| Error handling | Back-dating refused; first snapshot → no trends |
| Security | Internal-only stance; entitlement re-checked on read |
| Auditability | Snapshot history is itself the audit trail |
| Baseline | Time to assemble context; surprises in reviews |
| Success metrics | −70% research; zero unexplained surprises |
| Test scenarios | 3 snapshots; back-date; blocked finance |
| Failure modes | Stale sources; low identity match |
