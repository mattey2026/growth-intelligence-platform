# Skill Design Card — pricing-intelligence (v5.0, 24-item standard)

| Item | Detail |
|---|---|
| Skill name | pricing-intelligence |
| Business problem | Discount decisions on instinct; naive analytics misleading |
| Persona | AEs, Deal Desk, Finance |
| Trigger | Discount question; quote check |
| Inputs | Deal economics; history |
| Data sources | CPQ, CRM, ERP |
| Connectors / tools | pricing_model, anomaly |
| Context requirements | Policy, cost, approval matrix |
| Analytics | Realized price, discount anomalies |
| Predictive | Win probability vs discount (identified or assumed) |
| Reasoning | Confounding detection; robustness |
| Decision logic | Historical mode only if identified; else assumption range |
| Recommendations | Non-price levers first; test |
| Actions | Deal Desk draft |
| Approval | All approvals remain human |
| Output | Pricing view |
| Evidence | Model mode shown |
| Confidence | Robust / not robust |
| Error handling | Confounded → assumption mode |
| Security | Margin entitlement |
| Auditability | pricing_view, commercial_check |
| Baseline | Leakage, margin, rework |
| Success metrics | Margin up; rework −50% |
| Test scenarios | 10→15% not robust; approval path |
| Failure modes | Causal overreach |
