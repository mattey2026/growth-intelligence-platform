# Growth Intelligence Platform V7.1: Release Report

**Version:** 7.1.0 · **Date:** 30 September 2026 · **Status:** **Release candidate**

## Status in one paragraph
Every deliverable (D1–D25) is implemented, and every acceptance criterion that can be tested without model calls passes: **104/104 new tests** and **38/38 V7 regression tests**, with no regression. The official validator, strict YAML, registry, and reference checks also pass.

It is **not** labelled "Enterprise Growth & Decision Intelligence Complete". Section 26 permits that label only when every criterion is met, and three criteria require the three new agents to execute *live* as sub-agents (D3, D5, D8, "executes successfully against a representative account"). That needs your Claude account, so it has not been verified here. The deterministic pipelines those agents run are fully tested, and four live eval cases are ready (`bash tests/run_agent_tests.sh`, step 5). Decision-framework adaptation by business model is also PARTIAL (see Limitations).

---

## 1. Architecture

### What changed and why
| Change | Why |
|---|---|
| Marketing Intelligence (skill, agent, `marketing_signals.py`) | Marketing activity was not visible at account level, and attribution tends to be overstated. Influence is now labelled CORRELATION unless a holdout exists |
| Financial Intelligence (skill, agent, `financial_intel.py`) | Account strategy lacked the customer's own financial story, and LLM arithmetic is unreliable. All metrics are computed in code, with provenance, and missing values are reported, not estimated |
| Competitive Thread Intelligence (skill, agent, `competitive_threads.py`) | Competitor signals were isolated observations. The persistent CompetitiveThread joins them into one evolving story |
| Cross-domain correlation (`cross_domain_correlator.py`, patterns P1–P5) | Growth and risk usually show up across domains, not within one |
| Digital Twin domains, cross-domain delta, typed memory objects | Knowing *what changed, where*, and re-computing only that |
| Opportunity builder (11 fields) and account plan builder (12 sections) | Integrated outputs where every conclusion has evidence and values are sized only with a basis |
| Evidence contract (`evidence_validator.py claims`) | Enforce FACT / INFERENCE / CORRELATION / HYPOTHESIS / PREDICTION / RECOMMENDATION and reject fabrication |
| Registry-driven discovery (`serves_intents`) | New or customer agents join plans without planner changes; DISABLED agents are dropped |
| Trace events and `trace.py check` | End-to-end traceability, request → outcome |

### Integration points
The orchestrator's account-strategy chain runs:
1. context → memory → delta;
2. the account, relationship, market, **financial, marketing, and competitive-thread** agents, in parallel;
3. `cross_domain_correlator` (T0) → opportunity agent (T3) → twin snapshot (T0) → account plan (T3);
4. evidence validation → governance → decision framing → action prep → policy gate → memory.

Each new engine writes typed objects into the same memory file, and those objects feed the twin, the delta, and the next run. The Sanofi end-to-end test exercises this chain.

### Counts
| Item | V7 | V7.1 |
|---|---|---|
| Skills | 30 | **33** (3 new, 8 upgraded) |
| Domain agents | 17 | **20** |
| Registry entries (domain + 4 tier agents + orchestrator) | 22 | **25** |
| Agent files | 21 | **24** |
| Live eval cases | 8 | **12** |

## 2. Deliverables status
| # | Deliverable | Status | Evidence |
|---|---|---|---|
| D1 | Plugin package | IMPLEMENTED | `claude plugin validate` passes (plugin and agents); strict YAML; registry OK; 0 duplicates, orphans, or broken references; all V7 skills and agents present; V7 38/38. *Loading in a live Claude Code session is not tested here* |
| D2 | Marketing Intelligence skill | IMPLEMENTED | All required sections; MKT 1–11 |
| D3 | Marketing Intelligence agent | IMPLEMENTED; **live execution NOT VERIFIED** | Registry-discoverable (ORC 3, 5, 6); least privilege (EVG 7); pipeline tested (MKT); eval `marketing-agent` ready |
| D4 | Financial Intelligence skill | IMPLEMENTED | FIN 1–13; Sanofi metrics match reported figures |
| D5 | Financial Intelligence agent | IMPLEMENTED; **live execution NOT VERIFIED** | T0 math, T2/T3 interpretation in the manifest; sensitivity controls (EVG 7–8); eval `financial-agent` ready |
| D6 | Competitive Thread skill | IMPLEMENTED | THR 1–18 and 7b |
| D7 | Persistent CompetitiveThread | IMPLEMENTED | All required fields; survives processes (THR 15); three signals form one thread (THR 2) |
| D8 | Competitive Thread agent | IMPLEMENTED; **live execution NOT VERIFIED** | The signal → lookup → match → update → validate → confidence → action → persist chain is tested (THR); eval `competitive-thread-agent` ready |
| D9 | Cross-domain correlation | IMPLEMENTED | P1–P5 detected; emerging patterns with capped confidence; memory; routing (COR 1–11) |
| D10 | Orchestrator integration | IMPLEMENTED | All six prompts discover the new agents with no names given; plans correctly ordered (ORC 1–8) |
| D11 | Account Intelligence upgrade | IMPLEMENTED | 12 sections, 0 conclusions without evidence (XF D21.2–3) |
| D12 | Digital Twin upgrade | IMPLEMENTED | 8 domains; 5 states; updates on change; "what changed" (TWN 1–5) |
| D13 | Memory model | IMPLEMENTED | 9 required types plus 2 more; all 10 properties tested (MEM 1–6) |
| D14 | Cross-domain delta | IMPLEMENTED | New, changed, deleted, corrected, contradictory; unchanged domains skipped (TWN 3–4) |
| D15 | Opportunity discovery | IMPLEMENTED | 11 fields; no unsupported value as fact (XF D15 ×2) |
| D16 | Evidence contract | IMPLEMENTED | Six types; rejects or flags each named case (EVG 1–6) |
| D17 | Governance | IMPLEMENTED (enforcement procedural, see Security) | Negative tests: unauthorized agents and users are denied (EVG 7–9) |
| D18 | Observability | IMPLEMENTED | All 9 events; complete chain verified; incomplete traces detected (OBS 1–3) |
| D19 | Registry | IMPLEMENTED | 0 duplicate IDs, missing references, or orphans; dependencies resolve |
| D20 | Test suite | IMPLEMENTED | 104 new tests (76 required); every area at or above its minimum |
| D21 | Sanofi end-to-end | IMPLEMENTED (deterministic) | XF D21.1–6. Real public financials; internal data synthetic and labelled; no fabrication |
| D22 | Business-model adaptability | IMPLEMENTED; **decision framework PARTIAL** | KPIs, customer model, marketing, financial, and opportunity logic adapt (XF D22.1–3) |
| D23 | Missing data | IMPLEMENTED | All 7 cases (XF D23.1–7) |
| D24 | Documentation | IMPLEMENTED | README, ARCHITECTURE, CHANGELOG, CONNECTORS, agent and skill registries, memory model (25 copies plus docs/15), tests/README, evals/README; counts verified against the code |
| D25 | Release report | IMPLEMENTED | This document |

## 3. Testing
```text
V7 regression:   38 / 38 PASS   (30 V7 scenarios + 8 V6.1 regression checks)
V7.1:           104 / 104 PASS
Total:          142 / 142 PASS
```

| V7.1 area | Pass | Required |
|---|---|---|
| Marketing | 11/11 | 10 |
| Financial | 13/13 | 10 |
| Competitive threads | 19/19 | 16 |
| Correlation | 11/11 | 10 |
| Orchestration | 8/8 | 5 |
| Digital twin | 5/5 | 5 |
| Memory | 6/6 | 5 |
| Evidence and governance | 10/10 | 5 |
| Observability | 3/3 | — |
| Cross-functional | 18/18 | 10 |

**Structural:**
- `claude plugin validate .` and `./agents` both pass (Claude Code 2.1.284).
- Strict YAML: OK. Registry: OK (25 agents, 0 errors).
- 33/33 skills valid.
- 0 duplicate skill names or agent IDs, 0 orphans, 0 broken references (including every `scripts/…` path in a SKILL.md).
- All Python files compile.

**Live evals: not run here.** 12 cases are ready, 4 of them new.

### Defects found and fixed during V7.1 testing
The first full run passed 87/102. Every failure was diagnosed rather than patched over.

| Defect | Type | Effect before the fix |
|---|---|---|
| Marketing window helper received the wrong argument type | Engine | Crash |
| Thread `save` did not serialize structured fields | Engine | Crash |
| **Asymmetric thread-family matching** | Engine | One competitor story split into two threads (the D7 criterion failed) |
| CompetitiveEvent stored without confidence | Engine | Memory objects not confidence-scored |
| Trace order check forced agent spans before skill spans | Engine | Valid traces rejected |
| Account-plan evidence stored as bare strings | Engine | Validator could not verify sourced facts |
| **Thread momentum and confidence counted counter-evidence as support** | Engine | A threat stayed "accelerating" after two strong counter-signals |
| **Opportunity threads treated competitor weakness as counter-evidence** (found by reading the output, not by a test) | Engine | A real opportunity scored confidence 0.1; regression test 7b added |
| Conflicts mode rejected list inputs | Engine | Crash on a natural input form |
| **Planner listed steps before their dependencies** (found in the plan printout) | Engine | Misleading execution order; test ORC 8 added |
| Wrong expectations: two-campaign overwrite, 11 vs 12 stored signals (the unclassified one is kept), result-order sensitivity; a generator scoping bug; a missing "emerging" scenario | Test | Correct engine behaviour reported as failure |

## 4. Security and governance
**Permissions.** The three agents are least-privilege:

| Agent | Allowed data | Autonomy | Actions |
|---|---|---|---|
| marketing-intelligence-agent | marketing_data, crm | 1 | Internal notification only |
| financial-intelligence-agent | financial_data, public_filings, web | 0 | None |
| competitive-thread-agent | crm, transcripts, rfps, web | 1 | CRM task, internal notification |

None has write access to memory; the orchestrator is the single writer.

**Sensitivity.**
- Non-public financials are tagged `financial_confidential`. Access needs both the `financial_data` source and the `financial_confidential` clearance (granted to manager and CFO, not to seller).
- Public filings are separated as `public_filings`.

**Negative tests passed:**
- The marketing agent and the relationship agent are denied financial data.
- The financial agent is denied marketing data.
- A seller is denied confidential financials.
- A CFO is allowed.
- The registry refuses financial data to the thread agent.
- Threads and memory objects refuse another tenant.

**Known gaps:**
1. **Gate enforcement is procedural.** The orchestrator must call `policy_gate.py`; nothing in the runtime blocks a tool call that skips it. This is carried from V7 and is V8 item 1.
2. **PII.** Marketing signals carry contact IDs and roles and fall under the existing `pii` class, but there is **no redaction or masking** in stored objects.
3. **ABAC** covers region and ownership only.
4. The evidence validator catches fabrication *against the sources it is given*; it cannot detect a fabricated source.

## 5. Performance
**Measured** on the sandbox (single run, Sanofi fixtures):

| Engine | Time |
|---|---|
| financial_intel | 90 ms |
| marketing_signals | 66 ms |
| competitive_threads ingest | 37 ms |
| cross_domain_correlator | 33 ms |
| opportunity_builder | 29 ms |
| twin snapshot | 39 ms |
| account_plan_builder | 33 ms |
| agent_planner | 112 ms |

The V7.1 suite takes about 6.5 s and the V7 suite about 5.1 s.

**Model usage (planned, not measured).** The Sanofi strategy plan has 21 steps:
- **T0: 8 · T1: 2 · T2: 7 · T3: 3**;
- plus 1 *conditional* T4 challenge, which runs only if confidence is below 0.6, evidence conflicts, or impact is $5M or more.

All financial, marketing, thread, correlation, twin, delta, sizing, and plan-assembly calculations are T0 (code).

**Token and cost.** The planner's *estimate* is 206.6 relative cost units for this plan. **No token or cost figures were measured**, because no live model calls were made. Real figures come from the live eval run (`trace.py` records tokens and cost per step).

## 6. Known limitations
1. **Live agent execution not verified** (D3, D5, D8, and the live form of D10 and D21). This is the reason the release is not labelled Complete.
2. **Decision-framework adaptation by business model is PARTIAL.** KPIs, marketing, finance, customer model, and opportunity logic adapt. Decision memos use one framework for all models and cite model-specific KPIs only through their inputs.
3. **Sanofi internal data is synthetic.** Contacts, marketing touches, competitor signals, contracts, and whitespace are invented for testing and labelled `SYNTHETIC` in every record. Only the financial facts and events are real (cited). Net debt comes from a secondary source (confidence 0.7).
4. **Heuristic thresholds.** Engagement materiality (25%), intent surge (2×), thread momentum windows (60/90 days), confidence weights, and next-event rules are documented heuristics, not calibrated on outcome data.
5. **Attribution is correlation.** Campaign influence is a linear touch share. A causal estimate is used only when a holdout result is supplied.
6. **Single currency.** There is no FX normalization: facts for one entity must share a currency.
7. **No live connectors are bundled.** Marketing and finance data arrive as files, user-connected MCP tools, or cited research.
8. **Gate enforcement is procedural, and PII is not redacted** (Security, gaps 1–2).

## 7. V8 recommendations (not implemented today)
1. A PreToolUse hook that blocks consequential tools unless `policy_gate.py` allowed the request (hard enforcement).
2. Run the 12 live eval cases in CI with recorded token and cost; promote agents on eval scores.
3. PII redaction and masking for stored marketing objects and traces.
4. Calibrate thread momentum, confidence, and next-event rules on recorded `CompetitiveOutcome` data.
5. Business-model-specific decision frameworks (for example unit economics for B2C, channel economics for B2B2C).
6. Holdout and MMM integration so campaign influence can move from correlation to causal estimates at scale.
7. Currency normalization for multi-currency financial facts.
8. Reference connectors (MAP, ERP or FP&A, filings) with field mappings to the V7.1 input schemas.

## 8. Definition of Done (Section 26)
| Item | Status |
|---|---|
| V7 package preserved | ✅ (38/38; all V7 skills and agents present) |
| Marketing Intelligence implemented | ✅ |
| Marketing Intelligence Agent implemented | ✅ implemented · ⚠️ live execution not verified |
| Financial Intelligence implemented | ✅ |
| Financial Intelligence Agent implemented | ✅ implemented · ⚠️ live execution not verified |
| Competitive Thread Intelligence implemented | ✅ |
| CompetitiveThread persisted in Business Memory | ✅ |
| Competitive Thread Agent implemented | ✅ implemented · ⚠️ live execution not verified |
| Growth Signal Orchestrator upgraded | ✅ |
| Business Orchestrator upgraded | ✅ |
| Account Intelligence upgraded | ✅ |
| Digital Twin upgraded | ✅ |
| Business Memory upgraded | ✅ |
| Delta Intelligence upgraded | ✅ |
| Opportunity Discovery upgraded | ✅ |
| Evidence validation upgraded | ✅ |
| Governance integrated | ✅ (procedural enforcement) |
| Observability integrated | ✅ |
| Registry updated | ✅ |
| 76+ new tests implemented | ✅ (104) |
| Existing V7 tests pass | ✅ |
| New V7.1 tests pass | ✅ |
| Sanofi end-to-end test passes | ✅ (deterministic chain) |
| B2B / B2C / B2B2C adaptability tests pass | ✅ (decision framework PARTIAL) |
| Missing-data tests pass | ✅ |
| Documentation updated | ✅ |
| Release report produced | ✅ |
| Plugin package validates successfully | ✅ |

**To close the remaining items:** install the plugin in Claude Code, run `bash tests/run_agent_tests.sh`, and check that the four V7.1 eval cases pass. If they do, every criterion is met and the release can carry the full label.

---

## Appendix A: File-by-file list (V7 → V7.1)
### New files (95)

**Skills, agents, registry, docs, tests, evals, fixtures:**

- `agents/competitive-thread-agent.md`
- `agents/financial-intelligence-agent.md`
- `agents/marketing-intelligence-agent.md`
- `docs/15-v71-intelligence.md`
- `evals/competitive-thread-agent/case.yaml`
- `evals/competitive-thread-agent/fixture.sh`
- `evals/competitive-thread-agent/graders/answer-quality.md`
- `evals/competitive-thread-agent/graders/delegates-to-agent.md`
- `evals/competitive-thread-agent/graders/no-t4-by-default.md`
- `evals/competitive-thread-agent/prompt.md`
- `evals/financial-agent/case.yaml`
- `evals/financial-agent/fixture.sh`
- `evals/financial-agent/graders/answer-quality.md`
- `evals/financial-agent/graders/delegates-to-agent.md`
- `evals/financial-agent/graders/no-t4-by-default.md`
- `evals/financial-agent/prompt.md`
- `evals/fixtures/growth_memory_v7.db`
- `evals/fixtures/sanofi_bundle_SYNTHETIC.json`
- `evals/fixtures/sanofi_campaigns_SYNTHETIC.json`
- `evals/fixtures/sanofi_competitor_signals_SYNTHETIC.json`
- `evals/fixtures/sanofi_contacts_SYNTHETIC.json`
- `evals/fixtures/sanofi_events_PUBLIC.json`
- `evals/fixtures/sanofi_financials_PUBLIC.json`
- `evals/fixtures/sanofi_initiatives.json`
- `evals/fixtures/sanofi_marketing_SYNTHETIC.json`
- `evals/fixtures/sanofi_opps_SYNTHETIC.json`
- `evals/fixtures/sanofi_relationship_SYNTHETIC.json`
- `evals/marketing-agent/case.yaml`
- `evals/marketing-agent/fixture.sh`
- `evals/marketing-agent/graders/answer-quality.md`
- `evals/marketing-agent/graders/delegates-to-agent.md`
- `evals/marketing-agent/graders/no-t4-by-default.md`
- `evals/marketing-agent/prompt.md`
- `evals/sanofi-strategy-v71/case.yaml`
- `evals/sanofi-strategy-v71/fixture.sh`
- `evals/sanofi-strategy-v71/graders/answer-quality.md`
- `evals/sanofi-strategy-v71/graders/delegates-to-agent.md`
- `evals/sanofi-strategy-v71/graders/no-t4-by-default.md`
- `evals/sanofi-strategy-v71/graders/uses-competitive-thread-agent.md`
- `evals/sanofi-strategy-v71/graders/uses-financial-intelligence-agent.md`
- `evals/sanofi-strategy-v71/graders/uses-marketing-intelligence-agent.md`
- `evals/sanofi-strategy-v71/prompt.md`
- `registry/manifests/competitive-thread-agent.yaml`
- `registry/manifests/financial-intelligence-agent.yaml`
- `registry/manifests/marketing-intelligence-agent.yaml`
- `registry/skill-registry.json`
- `skills/competitive-thread-intelligence/SKILL.md`
- `skills/financial-intelligence/SKILL.md`
- `skills/marketing-intelligence/SKILL.md`
- `skills/marketing-intelligence/references/signal-taxonomy.md`
- `tests/README.md`
- `tests/fixtures/b2b2c_channel_SYNTHETIC.csv`
- `tests/fixtures/b2b2c_marketing_SYNTHETIC.json`
- `tests/fixtures/b2c_financials_SYNTHETIC.json`
- `tests/fixtures/b2c_marketing_SYNTHETIC.json`
- `tests/fixtures/customers.csv`
- `tests/fixtures/orders.csv`
- `tests/fixtures/sanofi_bundle_SYNTHETIC.json`
- `tests/fixtures/sanofi_campaigns_SYNTHETIC.json`
- `tests/fixtures/sanofi_competitor_signals_SYNTHETIC.json`
- `tests/fixtures/sanofi_contacts_SYNTHETIC.json`
- `tests/fixtures/sanofi_events_PUBLIC.json`
- `tests/fixtures/sanofi_financials_PUBLIC.json`
- `tests/fixtures/sanofi_initiatives.json`
- `tests/fixtures/sanofi_marketing_SYNTHETIC.json`
- `tests/fixtures/sanofi_opps_SYNTHETIC.json`
- `tests/fixtures/sanofi_relationship_SYNTHETIC.json`
- `tests/fixtures/transformation_events_SYNTHETIC.json`
- `tests/fixtures/transformation_financials_SYNTHETIC.json`
- `tests/run_v71.py`

**New script copies** (one engine, placed in each skill that runs it):

- `account_plan_builder.py` → account-intelligence-swot-planning, business-orchestrator
- `competitive_threads.py` → business-memory, business-orchestrator, competitive-thread-intelligence, growth-signal-orchestrator
- `cross_domain_correlator.py` → business-orchestrator, growth-signal-orchestrator, marketing-intelligence
- `domain_delta.py` → business-orchestrator, customer-digital-twin, data-intelligence
- `evidence_validator.py` → competitive-thread-intelligence, financial-intelligence, marketing-intelligence
- `financial_intel.py` → business-orchestrator, financial-intelligence
- `marketing_signals.py` → business-orchestrator, marketing-intelligence
- `memory_graph.py` → competitive-thread-intelligence, financial-intelligence, marketing-intelligence
- `opportunity_builder.py` → account-intelligence-swot-planning, business-orchestrator, growth-opportunity-discovery

### Modified files (119)

- `.claude-plugin/plugin.json`
- `ARCHITECTURE.md`
- `CHANGELOG.md`
- `CONNECTORS.md`
- `README.md`
- `docs/00-index.md`
- `evals/README.md`
- `policy/tenant-policy.example.yaml`
- `registry/agent-registry.json`
- `skills/account-intel-outreach/references/memory-model.md`
- `skills/account-intelligence-swot-planning/SKILL.md`
- `skills/account-intelligence-swot-planning/references/memory-model.md`
- `skills/business-context-discovery/references/memory-model.md`
- `skills/business-intelligence-copilot/references/memory-model.md`
- `skills/business-memory/SKILL.md`
- `skills/business-memory/references/memory-model.md`
- `skills/business-orchestrator/SKILL.md`
- `skills/business-watch/references/memory-model.md`
- `skills/competitive-intelligence/references/memory-model.md`
- `skills/customer-digital-twin/SKILL.md`
- `skills/customer-digital-twin/references/memory-model.md`
- `skills/daily-growth-briefing/references/memory-model.md`
- `skills/data-intelligence/SKILL.md`
- `skills/data-intelligence/references/memory-model.md`
- `skills/deal-intelligence/references/memory-model.md`
- `skills/executive-command-center/references/memory-model.md`
- `skills/growth-opportunity-discovery/SKILL.md`
- `skills/growth-opportunity-discovery/references/memory-model.md`
- `skills/growth-signal-orchestrator/SKILL.md`
- `skills/growth-signal-orchestrator/references/memory-model.md`
- `skills/knowledge-intelligence/references/memory-model.md`
- `skills/market-intelligence/references/memory-model.md`
- `skills/meeting-follow-through/references/memory-model.md`
- `skills/meeting-intelligence-brief/references/memory-model.md`
- `skills/pipeline-forecast-intelligence/references/memory-model.md`
- `skills/platform-admin/SKILL.md`
- `skills/pricing-intelligence/references/memory-model.md`
- `skills/relationship-intelligence/references/memory-model.md`
- `skills/renewal-expansion-radar/references/memory-model.md`
- `skills/rfp-response-composer/references/memory-model.md`
- `skills/scenario-planner/references/memory-model.md`
- `skills/win-loss-intelligence/references/memory-model.md`
- `tests/fixtures/tenant-policy.example.yaml`
- `tests/run_agent_tests.sh`

**Modified script copies** (the same updated engine in every skill that carries it):

- `agent_planner.py` (1 copies) → business-orchestrator
- `context_discovery.py` (3 copies) → business-context-discovery, business-orchestrator, data-intelligence
- `evidence_validator.py` (30 copies) → account-intel-outreach, account-intelligence-swot-planning, action-center, business-context-discovery, business-intelligence-copilot, business-memory, business-orchestrator, business-watch, competitive-intelligence, customer-digital-twin, daily-growth-briefing, data-intelligence, deal-intelligence, decision-intelligence, executive-command-center, growth-opportunity-discovery, growth-signal-orchestrator, knowledge-intelligence, market-intelligence, meeting-follow-through, meeting-intelligence-brief, pipeline-forecast-intelligence, platform-admin, pricing-intelligence, relationship-intelligence, renewal-expansion-radar, rfp-response-composer, scenario-planner, solution-architecture, win-loss-intelligence
- `kpi_engine.py` (4 copies) → business-intelligence-copilot, business-orchestrator, daily-growth-briefing, executive-command-center
- `memory_graph.py` (30 copies) → account-intel-outreach, account-intelligence-swot-planning, action-center, business-context-discovery, business-intelligence-copilot, business-memory, business-orchestrator, business-watch, competitive-intelligence, customer-digital-twin, daily-growth-briefing, data-intelligence, deal-intelligence, decision-intelligence, executive-command-center, growth-opportunity-discovery, growth-signal-orchestrator, knowledge-intelligence, market-intelligence, meeting-follow-through, meeting-intelligence-brief, pipeline-forecast-intelligence, platform-admin, pricing-intelligence, relationship-intelligence, renewal-expansion-radar, rfp-response-composer, scenario-planner, solution-architecture, win-loss-intelligence
- `registry.py` (3 copies) → action-center, business-orchestrator, platform-admin
- `trace.py` (2 copies) → business-orchestrator, platform-admin
- `twin_state.py` (2 copies) → business-orchestrator, customer-digital-twin

### Removed files (2)

- `tests/last-offline-results.json` (test-run artifact; removed by the packaging rule, not a capability)
- `tests/last-offline-run.json` (test-run artifact; removed by the packaging rule, not a capability)