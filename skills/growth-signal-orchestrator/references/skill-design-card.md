# Skill Design Card — growth-signal-orchestrator (v5.0, 24-item standard)

| Item | Detail |
|---|---|
| Skill name | growth-signal-orchestrator |
| Business problem | Cross-functional signals are never connected |
| Persona | Account teams, leaders, CS, RevOps |
| Trigger | Portfolio scan; twin changes; watches; 'connect the dots' |
| Inputs | Signals in window; custom patterns |
| Data sources | All producers via the signal bus |
| Connectors / tools | signal_correlator |
| Context requirements | Pattern library; window |
| Analytics | Pattern matching, function diversity |
| Predictive | Triggers churn, expansion, revenue at risk |
| Reasoning | Story, value at stake, hypotheses, alternative explanations |
| Decision logic | min_matched, min_functions, strength |
| Recommendations | Intervention per function owner |
| Actions | Triggered skills; approved workflows |
| Approval | Every workflow and action |
| Output | Pattern report |
| Evidence | Dated sequence with sources |
| Confidence | From the number of independent functions |
| Error handling | Single-function data → state which sources are missing |
| Security | Filter to entitled signals before correlating |
| Auditability | Pattern ledger |
| Baseline | Risk lead time; precision vs history |
| Success metrics | ≥ 60% precision; +4 weeks lead time |
| Test scenarios | ACME risk; GLOBEX opportunity; single signal → none |
| Failure modes | Over-firing; spurious correlation |
