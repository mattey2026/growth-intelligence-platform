# 11. Growth Signal Orchestrator: Design

**Purpose:** correlate signals across skills, systems, and functions into patterns with business meaning, then trigger analysis, recommend actions, and measure outcomes. It is not an alert engine; a single signal is not a pattern.

## Pipeline
```
Signal producers ──► Signal bus (normalized, permission-tagged) ──► Correlation (pattern library)
  ──► Contextual reasoning (twin context, value at stake, causes, alternatives)
  ──► Triggers (predictions, skills, twin update) ──► Intervention (owners per function, approvals)
  ──► Outcome measurement (ledger; pattern precision) ──► Pattern tuning
```

| Component | Implementation |
|---|---|
| Signal schema | `references/signal-vocabulary.md`: entity, signal, direction, magnitude, date, function, source, evidence |
| Producers | Twin change log, deal-intelligence, renewal radar, relationship, competitive, pricing, business watch, connectors (marketing, usage, ITSM, ERP), external research |
| Pattern library | 6 defaults (compound customer risk, expansion readiness, competitive displacement, executive access loss, service-driven commercial opportunity, margin erosion), plus organization-specific patterns in JSON |
| Correlation engine | `signal_correlator.py`: condition matching in a window; minimum matched conditions and minimum independent functions; weighted strength; confidence from function diversity; dated sequence; unconfirmed conditions |
| Reasoning | Claude: business story, value at stake, hypotheses about causes (never asserting cause from order alone), alternative explanations, checks |
| Triggers | Predictions (churn, expansion, revenue at risk…) and skills per pattern |
| Actions | Prepared by the owning skills; approval-gated; workflows only after approval |
| Measurement | Pattern → intervention → outcome in the ledger; quarterly precision per pattern; retune or retire weak patterns |

**Tested behaviour:** ACME (5 functions) → compound risk, High confidence. GLOBEX → expansion readiness, High. INITECH (a single competitor mention) → no pattern.
