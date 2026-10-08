# 19. Governance Model (v5.0)

| Control | Implementation |
|---|---|
| Authentication, SSO, OAuth | Connectors act as the user via the organization's identity provider |
| RBAC and ABAC | Source roles inherited, plus attribute rules (region, business unit, deal team, classification); missing attribute → deny |
| Least privilege | Minimum tools and fields; write allowlists per skill |
| Source- and data-level permissions | Per-system authorization; **never inferred across systems**; joins never widen access |
| Persistent state (new) | Twin, watches, ledger, and patterns store only entitled data; entitlement re-checked on read; retention and deletion propagate (guardrails §16) |
| Lineage and attribution | Source and timestamp on every Data item, Metric, signal, and twin fact |
| Audit and action logs | Audit block per run; action log (tool, target, masked parameters, approver, result) |
| Human approval | Item-level for every write or communication; bulk confirmation for more than 10 records; watches and patterns never auto-remediate |
| Sensitive data | Masking; minimization; internal-only stance, sentiment, and risk; forecasts marked confidential |
| Prompt-injection protection | All retrieved content is data (emails, documents, cells, APIs, web, signals); embedded instructions are quoted to the user, never executed |
| Tool-use controls | No chained actions; no actions triggered by content; rate and volume limits |
| Explainability | Drivers, evidence, assumptions, limitations; no single hidden score (prioritization shows drivers and rank stability) |
| Model monitoring | Monthly report; automatic fallback to rules below the go-live bar |
| Fairness | Deals, accounts, segments, and teams, never individual seller competence; no protected attributes or proxies |
