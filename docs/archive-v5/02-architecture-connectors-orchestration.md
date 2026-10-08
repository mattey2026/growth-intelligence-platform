# 3, 17, 18. v5 Architecture, Connector/Plugin Architecture, Orchestration

```
┌───────────────────────────────────────────────────────────────────────────────────┐
│ EXPERIENCE   natural language · daily briefing · watches · (P2) command center    │
├───────────────────────────────────────────────────────────────────────────────────┤
│ WORKFLOW SKILLS  deal · pipeline/forecast · account plan · retention · meetings · │
│                  scenarios · outreach · RFP                                       │
├───────────────────────────────────────────────────────────────────────────────────┤
│ GROWTH ENGINES   opportunity discovery · relationship · competitive · pricing ·   │
│                  business watch · (P1) economics, decision, next-best-account ·   │
│                  (P2) demand, product, partner, capacity, leakage                 │
├───────────────────────────────────────────────────────────────────────────────────┤
│ INTELLIGENCE SERVICES  growth signal orchestrator · BI copilot · win/loss learning│
├───────────────────────────────────────────────────────────────────────────────────┤
│ CONTEXT      customer digital twin · knowledge intelligence · (P3) growth graph   │
├───────────────────────────────────────────────────────────────────────────────────┤
│ ANALYTICS & PREDICTION  18 deterministic engines · prediction ledger · monitoring │
├───────────────────────────────────────────────────────────────────────────────────┤
│ DATA         discover → profile → map → validate → normalize → resolve (10 entities)│
├───────────────────────────────────────────────────────────────────────────────────┤
│ CONNECT      MCP connectors, per-system authorization, least privilege            │
├───────────────────────────────────────────────────────────────────────────────────┤
│ SOURCES      any CRM · ERP · ITSM · HR · marketing · product · warehouse/lake ·   │
│              SQL · REST/GraphQL · Excel/CSV/Sheets · docs · email · calendar      │
└───────────────────────────────────────────────────────────────────────────────────┘
 GOVERNANCE (all layers): identity · RBAC/ABAC · lineage · approvals · audit · injection & tool controls · model monitoring
 LEARNING LOOP: outcomes → win/loss → ledger → pattern precision → recalibration
```

## Connector/plugin architecture
- **Connectors**: MCP servers per system, configured per organization, authenticated as the user. None is an architectural dependency: files, SQL, or APIs can substitute for any of them.
- **Tool selection**: minimum tools; system of record first; compute in code; retrieved content is data; write tools only after approval; bulk-action confirmation.
- **Contracts** (versioned JSON): `account_state` v2 (twin), `growth_patterns`, `growth_opportunities`, `relationship_view`, `competitive_view`, `pricing_view`, `winloss_learning`, `bi_answer`, `knowledge_answer`, `watch_results`, `deal_intelligence`, `deal_risk`, `forecast_view`, `briefing`, `dataset_profile`, `deal_delta`, `prediction_ledger`, and others.
- **Engines** (18 scripts, numpy and pandas only):
  - data: profiler, normalize, entity_resolver;
  - context: twin_update, knowledge_catalog;
  - intelligence: signal_correlator, driver_tree, winloss_analyzer, competitive_watch;
  - prediction: deal_risk_model, propensity_model, ts_forecast, forecast_sim, pipeline_whatif, anomaly_detect;
  - prescriptive: opportunity_scorer, whitespace_matrix, account_prioritizer, pricing_model, scenario_model, signal_ranker, watch_evaluator, account_change_diff.

## Orchestration
See `references/orchestration.md` for the routing table, the 7 composition rules, and v4 → v5 backward compatibility. Example of a composed outcome:

"Build the Acme account plan" → twin → orchestrator patterns → SWOT → relationship (executive coverage) → competitive → opportunity discovery → account economics → deal-intelligence (major deals) → plan → executive brief. The user asks once.
