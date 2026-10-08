# Signal Vocabulary (v5.0)

Normalized signals let every skill contribute to, and consume from, the Growth Signal Orchestrator and the Customer Digital Twin.

**Format:** `{"entity_id","signal","direction":"up|down|event","magnitude","date","function","source","evidence"}`

**Functions:** marketing · sales · cs · service · product · finance · operations · partner · external

| Signal | Direction | Typical source | Emitted by |
|---|---|---|---|
| marketing_engagement | up / down | Marketing automation | twin, demand intelligence |
| customer_investment | event | Web, filings, transcripts | opportunity discovery |
| new_executive / executive_sponsor_departed | event | CRM, email bounce, web | relationship-intelligence |
| executive_engagement / champion_engagement | up / down | Email, calendar | relationship-intelligence |
| single_threaded / unanswered_commitment | event | Interactions, deal_delta | relationship-intelligence |
| product_usage / product_adoption | up / down | Usage warehouse | twin, product intelligence |
| service_incidents / sla_breaches | up / down | ITSM | twin |
| recurring_issue_category | event | ITSM | twin |
| payment_disputes / dso | up / down | ERP | twin |
| gross_margin / cost_to_serve / discount_depth | up / down | ERP, CPQ | pricing, account economics |
| free_services | event | PSA, contracts | revenue leakage |
| competitor_mention | up / down | Transcripts, CRM, email | competitive-intelligence |
| rfp_issued / price_benchmark_request | event | Email, procurement | competitive-intelligence |
| competitor_contract_expiring | event | Transcripts, research | competitive-intelligence |
| whitespace_identified / offering_addresses_issue | event | whitespace_matrix, knowledge | opportunity discovery |
| renewal_within_180d | event | Contracts | twin |
| budget_available | event | Transcripts, email | deal-intelligence |
| deal_slip_risk_up / close_date_pushed | event | deal-intelligence | deal-intelligence |
| pipeline_creation | up / down | CRM | pipeline-forecast |

Extend the vocabulary per organization. Keep names in snake_case and stable over time.
