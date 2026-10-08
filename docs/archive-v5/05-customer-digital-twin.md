# 12. Customer Digital Twin: Design

**A persistent, time-aware model of each customer**: Current state → Historical state → Changes → Trends → Predictions → Recommended actions.

| Aspect | Design |
|---|---|
| Model | `account_state` v2.0 (company, business units, stakeholders, products, contracts, opportunities, revenue, margin, usage, service, marketing, financial behaviour, competitors, priorities, SWOT, 9 risk dimensions, predictions, discovered opportunities, signals, actions) |
| Storage | Append-only JSONL of snapshots in the data platform (P2: warehouse table plus Growth Graph) |
| Write path | Skills that assess an account write a snapshot, and emit signals for changed facts |
| Read path | `twin_update.py view`: current state, per-metric series, trends (slope per 30 days, confidence by number of snapshots), dated change log, how long each current risk has been present |
| Integrity | Refuses back-dating and duplicate as-of dates; the system of record wins on conflicts; lineage per fact |
| Questions answered | What changed · when · why it matters · what caused it (hypotheses) · what is likely next · what to do |
| Governance | Internal-only stance and risk; entitlement re-checked on read; retention policy |
| Refresh | On demand; scheduled (daily for strategic accounts, weekly otherwise); event-driven via watches |

**Tested behaviour:** 3 quarterly snapshots → dated changes (service risk low→medium on 30 Jun, →high on 28 Sep; sponsor departed 28 Sep; renewal probability 0.80→0.58); back-dating refused.
