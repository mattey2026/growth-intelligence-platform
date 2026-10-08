# 2. Business Context Discovery (Layer 0)

- **Scoring:** vocabulary (sheets, columns, categorical values, matched as whole words) plus structural evidence (revenue per customer, deal size, buyer roles, channels) produce a score for each of 10 business models. Confidence reflects both the share of evidence and the margin over the runner-up.
- **Confidence gate (0.6):** below the gate, the engine stops and asks targeted questions.
- **Seller vs customers:** the seller's industry is inferred from its offerings; customers' industries are reported separately.
- **Scale:** combines financial, commercial, organizational, and operational dimensions, never deal size alone. Caveats cover sample data and missing employee counts.
- **Persistence:** the profile is stored in memory. Reuse it unless new evidence contradicts it; changes are recorded as transitions.

## Test results
| Input | Result |
|---|---|
| Test workbook | **B2B, confidence 0.98** (roles CIO/CFO/COO/CTO, champion, contracts, negotiation; $8.1M revenue per customer; median deal $2.6M). Seller: *Technology & IT Services, hybrid software + managed services* (0.95). Customers: 12 industries. Scale: Enterprise (0.78; sample caveat, no employee count) |
| D2C sample | **D2C, 0.47**: below the gate, so it asks |
| Ambiguous table | **Undetermined, 0.0**: asks 3 questions |
