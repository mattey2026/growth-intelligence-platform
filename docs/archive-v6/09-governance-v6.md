# 9. Governance (v6 additions)

- **§17 Memory governance:**
  - entitlement checked on write and read;
  - business-role data only;
  - never imply memory that was not loaded;
  - corrections override inferences;
  - preferences only when set explicitly;
  - deletion propagates to derived facts.
- **§18 Routing transparency:** a run log for every major analysis; token figures labelled as estimates; no claims of routing where the surface cannot route.
- **§19 Decisions in force:** checked before recommending; conflicts are surfaced and routed to the decision owner.

All v5 controls continue (RBAC/ABAC, per-system authorization, prompt-injection protection, tool-use controls, approvals, audit, model monitoring).
