# 4. Governance and Security

| Control | Implementation | Status |
|---|---|---|
| Tenant isolation | One memory file per tenant, bound via `GROWTH_TENANT`; the policy gate checks the tenant | IMPLEMENTED (file level) |
| RBAC | `tenant-policy` roles with inheritance: actions, data sources, clearances | IMPLEMENTED |
| ABAC | Attribute rules (for example user.region vs record.region) | IMPLEMENTED (simple equality rules) |
| Agent / skill / tool / data / action permissions | Manifests + `registry.py can` + the gate + the generated tool allowlists | IMPLEMENTED |
| Agents inherit user permissions | The gate checks the **user's** role first, then the agent's allowlist; an agent never widens access | IMPLEMENTED |
| Action permissions and approvals | `policy/action-catalog.yaml` (risk, external, autonomy, auto_max, approver, floor) + `action_manager.py` state machine | IMPLEMENTED |
| Evidence sufficiency | The gate refuses actions below the tenant's confidence and evidence thresholds | IMPLEMENTED |
| Audit logging | `action_log`, the ledger, and execution traces | IMPLEMENTED (local files) |
| Prompt and agent injection defense | Packets separate USER TASK / SYSTEM POLICY / AGENT CONTRACT / `<data>` / TOOL RESULTS; `evidence_validator.py` scans data and results; agents cannot act | IMPLEMENTED (pattern-based scan + structural separation) |
| PII controls | Data sensitivity classes vs role clearance at the gate; guardrails §17 | PARTIAL (classification must be supplied by the connector or data owner) |
| Data lineage | Source on every fact and data source memory; the delta engine | PARTIAL (source-level, not column-level) |
| Retention | Memory compression; policy in guardrails | PARTIAL (no automatic purge schedule) |
| Secrets management and encryption | Delegated to the host (Claude connectors, OS / disk encryption, warehouse) | DESIGNED: the platform stores no credentials |
| Multi-tenant commercial model (Tenant → Users → Roles → Context → Memory → Agents → Skills → Sources → Policies → Connectors → Audit → Billing) | Per-tenant memory + policy + trace | PARTIAL: billing and usage hooks are in traces; no tenant service or UI |
