# 8. Continuous Watch, Stateful Alerts, and Learning

## Stateful alerts
FIRE_NEW → (acknowledged) → **UPDATE** only on material change → **SUPPRESS** otherwise → RESOLVED.

| Account | Review 2 result |
|---|---|
| A002 | Acknowledged after review 1. Review 2 sent an UPDATE, not a repeat: "remains in alert… renewal 47 → 33 days; Sev-1/2 cases 2 → 1" |
| A006 | SUPPRESS (no material change) |
| A012 | FIRE_NEW (Healthy → Watch) |

## Prediction → Actual → Error → Learning
O009 was predicted at 0.83 and closed won, an error of +0.17. The learning was recorded as a **proposed** rule and not applied: one outcome is not evidence, and 20 comparable outcomes are required.

## Memory-aware forecasting
Each forecast is stored as a prediction. The next review shows the previous forecast, the change, and the reason for it. Error statistics accumulate in the ledger.
