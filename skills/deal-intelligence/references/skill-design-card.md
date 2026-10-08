# Skill Design Card — deal-intelligence (v4.0, 24-item standard)

| Item | Detail |
|---|---|
| Skill name | deal-intelligence |
| Business problem | Deal reviews interrogate sellers rather than evidence; close plans are generic; slippage is found late |
| Persona | AEs, managers, deal teams |
| Trigger | "Review/help me win/close plan for <deal>"; red deal flagged |
| Inputs | Opportunity; history; evidence |
| Data sources | CRM, email/calendar, transcripts, documents, CPQ |
| Connectors / tools | deal_risk_model, buying-committee, deal-strategy, deal-desk |
| Context requirements | Sales methodology, stage exit criteria, approval matrix |
| Analytics | Velocity, stage progression, time in stage vs peers, evidence coverage |
| Predictive | Win and slip probability; close-date risk; cycle-time quantiles |
| Reasoning | Model vs evidence reconciliation; decision-process mapping |
| Decision logic | Red-flag rules R1–R9; walk-away test; approval path |
| Recommendations | Deal strategy, close plan, execution plan |
| Actions | Tasks, close-date and category proposals, mutual-plan draft, meeting request draft |
| Approval | Every field change and communication |
| Output | Deal Review → Strategy → Close Plan → Execution Plan |
| Evidence | Cited interactions and field history |
| Confidence | Backtest-based (standards §4) |
| Error handling | Thin history → rules; conflicts shown |
| Security | Hierarchy scoping |
| Auditability | Change sets + ledger |
| Baseline | Seller-commit slip AUC; review prep time |
| Success metrics | Slipped value flagged ≥ 4 weeks early; win rate; prep time |
| Test scenarios | Commit deal with no paper process; competitive stuck deal |
| Failure modes | Over-trust in the model; stale evidence |
