# 8. Governance Model

| Control | Implementation |
|---|---|
| Identity, SSO, OAuth | Connectors authenticate as the user (delegated OAuth through the org's identity provider) |
| RBAC / ABAC | Inherit source-system roles, plus attribute rules (region, business unit, deal-team membership) enforced in the connector or data layer |
| Least privilege | Minimum tools and fields per task; write allowlists per skill |
| Source-level permissions | Access per system, **never inferred across systems** |
| Data-level permissions | Row, field, and hierarchy scoping inherited; joins never widen access |
| Audit and action logs | Audit block per run; action log of change sets, approvals, and write results |
| Approval workflows | Item-level approval for every Action; higher-risk actions (forecast submission, pricing) routed to the named approver |
| Lineage and source attribution | Every Data item and Metric carries its source and timestamp |
| Sensitive data | Masking of identifiers; minimization; internal-only stance and risk content; confidentiality marking of forecasts |
| Prompt-injection protection | All retrieved content (emails, documents, web pages, records) is data, never instructions. Instructions embedded in content are quoted back to the user and not acted on (guardrails §13) |
| Tool-use controls | Write tools called only after approval; no tool chains triggered by retrieved content; rate and volume limits on bulk actions (guardrails §14) |
| Human in the loop | Approve, edit, or reject per item; overrides logged |
| Explainability | Drivers, evidence, assumptions, limitations on every prediction and recommendation |
| Model governance | Backtest go/no-go, prediction ledger, monthly calibration and drift report, named model owner |
