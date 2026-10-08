# Skill Design Card — win-loss-intelligence (v5.0, 24-item standard)

| Item | Detail |
|---|---|
| Skill name | win-loss-intelligence |
| Business problem | Lessons from outcomes are lost |
| Persona | Sales leaders, RevOps, enablement, product marketing |
| Trigger | Quarter close; 'why do we lose' |
| Inputs | Closed deals; interviews |
| Data sources | CRM, transcripts, surveys |
| Connectors / tools | winloss_analyzer |
| Context requirements | Factor definitions |
| Analytics | Rates with CIs, lift, p-values, drift, Pareto |
| Predictive | Features for win and slip models |
| Reasoning | Confounding and interaction checks |
| Decision logic | Reliable only if n ≥ 15 and p < 0.05; adoption only after backtest lift |
| Recommendations | Motion, qualification, pricing, product changes |
| Actions | Feed models; enablement drafts |
| Approval | Model feature adoption; process changes by the owning leader |
| Output | Learning report |
| Evidence | Deal-level |
| Confidence | CI per pattern |
| Error handling | Low reason completeness → capped |
| Security | No seller ranking |
| Auditability | winloss_learning contract |
| Baseline | Model AUC; win rate |
| Success metrics | AUC lift; win-rate change vs control |
| Test scenarios | Planted effects recovered; confounded discount |
| Failure modes | Spurious patterns; stale reasons |
