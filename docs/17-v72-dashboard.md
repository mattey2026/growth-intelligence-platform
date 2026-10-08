# Growth Intelligence Platform V7.2: Dashboard Intelligence + Claude Artifact

**Version:** 7.2.0 · **Date:** 30 September 2026 · **Status:** **Release candidate**
**Published demo:** Enterprise Growth Command Center — https://claude.ai/artifact/JVNAVZah1Fg7bt3Lmenb7Y

## Status in one paragraph
Every deliverable is built, and every acceptance criterion that can be tested without model calls passes:
- **83/83 dashboard tests**, run in headless Chromium against the rendered artifact;
- V7.1 **104/104** and V7 **38/38** (no regression), so **225/225** in total;
- the official validator, strict YAML and registry checks.

Two items are **not verified here**:
1. The dashboard agent running *live* as a sub-agent. It needs your Claude account; the eval case `dashboard-agent` is ready.
2. Ask Intelligence in the *published* page cannot send messages into the chat. It copies the question, with its dashboard context, for you to paste. Direct hand-off (`sendPrompt`) works only where the host provides it.

## 1–2. Skills
| Skill | Defines |
|---|---|
| **dashboard-intelligence** | Dashboard selection, composition, KPI and visualization selection, persona adaptation, metric definitions, insights, anomalies, trends, cross-domain intelligence, queries, drill-down, evidence, actions, scenarios, filtering, comparison, state, and design rules. Scripts: demo and production providers, `dashboard_builder.py` (T0), `dashboard_state.py`. References: design system, personas, metric definitions, cited demo financials |
| **artifact-dashboard-intelligence** | The renderer: `render_dashboard.py` plus template, CSS, core and widgets (23 widget types). It contains no business logic |

## 3. Agent
**dashboard-intelligence-agent.**
- **Tier:** T2 by default; T3 for strategic synthesis; T4 only for high-value executive synthesis.
- **Access:** read-only memory, no shell, no actions.
- **Role:** it designs the experience and reviews the contract. The orchestrator runs the T0 builder and renderer.
- **Discovery:** found through the `dashboard` intent. Five domain agents serve the intent through registry discovery.
- **Governance check:** the registry *rejected* my first manifest, which gave the agent shell access (the single-writer rule). It was corrected.

## 4–5. Dashboard Contract and object model
- **Schema:** `schemas/dashboard.schema.json` (JSON Schema 2020-12), with 18 object types. These include all 13 in the brief: Dashboard, DashboardWidget, DashboardLayout, DashboardFilter, DashboardQuery, DashboardInsight, DashboardMetric, DashboardSignal, DashboardOpportunity, DashboardRisk, DashboardAction, DashboardEvidence, DashboardScenario.
- **Common fields:** every measured object supports id, label, value, unit, trend, previous_value, confidence, source, timestamp, evidence, drill_down_target, plus claim type, facets and data mode.
- **Independence:** the contract contains no HTML, CSS or JavaScript (tested).

## 6. Growth Intelligence Design System
`references/dashboard-design-system.md`:
- **Color:** graphite and cool-white bases; one deep blue-teal analytical accent; a six-color categorical palette; semantic sentiment.
- **Type:** IBM Plex Sans and Condensed, with tabular numerals.
- **Layout:** a 12-column grid; light and dark themes on the same tokens.
- **Signature element:** a provenance mark on every material number.
- **Forbidden:** gradients, glass effects, Claude default colors, emojis, 3D charts. Tested against the CSS.

## 7–8. Renderer and Command Center
**Views:** Overview, Growth, Accounts, Pipeline, Customers, Competition, Market, Financial, Marketing, Operations, Decisions, Actions. The header, KPI strip and Ask Intelligence are persistent.

**Widgets:**
- KPI strip; State of the business; What changed; performance trend (6 metrics, actual, target, previous year and forecast, annotated);
- growth-driver tree; opportunity radar; risk matrix; competitive landscape; competitive threads with timeline;
- financial panel (cited metrics, margin bridge, expense mix, drivers, account economics, business-unit mix);
- marketing panel (engagement, executive, intent, campaigns as correlation, heatmap, timeline);
- relationship map; dynamic SWOT; 8-dimension health; actions; Scenario Lab; 8 comparison modes; sortable tables.

**Interaction:** drill-down, the evidence drawer, cross-filtering, saved views, light and dark themes.

## 9. Demo dataset
`demo_provider.py` runs the **real V7.1 engines** on demo inputs:

| Item | Count |
|---|---|
| Enterprise account (plus 2 peer accounts for comparison) | 1 |
| Competitors | 5 |
| Opportunities | 10 |
| Executives | 15 |
| Marketing signals | 20 |
| Financial signals | 15 (5 public + 10 account) |
| Competitive threads (formed by the engine) | 8 |
| Account changes (from `domain_delta.py`) | 27 |
| Performance series | 24 months |

Every demo record is labelled `DEMO DATA — NOT REAL CUSTOMER DATA`. The only real claims about Sanofi are its published FY2024–25 financials and events, each with its citation. No Sanofi program or person is invented: names are generic (Contact A, Competitor X).

## 10. Personas
Nine configurations: Investor, CEO, CFO, COO, CRO, Growth Ops, Sales Head, Sales Director, AE. One contract carries every persona's layout. Switching persona changes presentation only; the role, set by the tenant policy, decides data access.

## 11. Test suite (`tests/run_dashboard.py`)
| Area | Result | Required |
|---|---|---|
| Skill | 11/11 | 10 |
| Agent | 10/10 | 10 |
| Contract | 11/11 | 10 |
| Rendering | 10/10 | 10 |
| Cross-filter | 10/10 | 10 |
| Drill-down | 10/10 | 10 |
| Persona | 6/6 | 6 |
| Evidence | 5/5 | 5 |
| Scenario | 5/5 | 5 |
| Responsive/design | 5/5 | 5 |
| **Total** | **83/83** | **81** |

Regression: V7.1 104/104 and V7 38/38. **Total 225/225.**

Notable tests:
- The renderer displays a mutated contract value verbatim, which proves it does no computation.
- A seller's contract contains no account economics: the data is removed, not hidden.
- An invalid contract is refused.
- Production renders every view with explicit empty states.
- "What happens if…" opens the Scenario Lab.
- The state store is tenant-bound.
- There is no horizontal overflow at 1280, 1440, 1600 or 1920 in any view.

## 12. Visual QA results
Headless Chromium 141, with IBM Plex installed locally so screenshots match the published fonts.

| Check | 1280 | 1440 | 1600 | 1920 |
|---|---|---|---|---|
| Horizontal overflow, all 12 views | 0px | 0px | 0px | 0px |
| Truncated KPI labels, values or comparisons | 0 | 0 | 0 | 0 |
| Wrapped KPI footers | 0 | 0 | 0 | 0 |
| KPI label and value tops aligned | yes | yes (measured) | yes | yes |
| Rows summing to 12 columns (9 personas × 12 views) | yes | yes | yes | yes |
| Light and dark themes reviewed by screenshot | yes | yes | — | yes |

**Tablet (1024px):** widgets stack full width, with no overflow.

**Defects found by inspecting screenshots and fixed:**
- grid spans ignored;
- 339px overflow in Marketing;
- unreadable margin bridge;
- revenue axis starting at $0 (hid the June dip);
- radar label collisions and timeline label clipping;
- KPI misalignment and truncation;
- provenance marks clipped inside long source cells;
- dates wrapping;
- a "0.0pp" change shown in red.

## 13. Architecture
See `ARCHITECTURE.md` (Dashboard Intelligence layer). The demo and production providers feed **one** builder, which feeds the contract, which feeds the renderer. The orchestrator runs the T0 steps; the agent works at T2 only. Actions go through the orchestrator and the Action Center, never from the page.

## 14. Files created and modified
See Appendix A (generated by diffing V7.1 and V7.2): 33 created, 20 modified, 0 removed.

## 15. Known limitations
1. **Live agent execution is not verified.** Eval `dashboard-agent` is ready (`bash tests/run_agent_tests.sh`, step 6).
2. **Published-page hand-off.** Ask Intelligence and "Request approval" in the *published* artifact copy the question, with its context, for the chat. A direct send needs a host that provides `sendPrompt`. No reasoning happens in the page, either way.
3. **The narrative is templated (T0)** from computed facts. The agent may rephrase it at T2 (`contract_review`), keeping the evidence ids. That rephrasing is not exercised live here.
4. **Heuristics.** The health-dimension formulas, risk likelihood and impact rules, and anomaly thresholds are documented but not calibrated on outcomes.
5. **The production provider was tested on the V7.1 workbook** (2 opportunities, no billing history). It has not been tested against a live Salesforce org or ERP.
6. **Browser storage** holds per-viewer state in the published page. Server-side state (`dashboard_state.py`) is used by the orchestrator; the page itself does not sync to it.
7. **Dashboard refresh is manual.** Re-running the builder and re-publishing refreshes the page; there is no live data binding.
8. **Governance carried from V7:** the policy gate is enforced by procedure, and PII in marketing objects is not redacted.

## 16. V8 recommendations (not implemented today)
1. Live data binding: publish with the artifact database or state capability so the page refreshes from the orchestrator without republishing.
2. In-page approval flow, connected to the Action Center, with the human approval recorded.
3. Calibrate health, risk and anomaly heuristics on recorded outcomes.
4. Reference connectors (Salesforce, ERP billing, service desk) mapped to the production-provider inputs.
5. A React or Next.js renderer of the same contract, to prove renderer independence in production.
6. Carried from V7.1: hard enforcement of the policy gate (PreToolUse hook) and PII redaction.

---

## Appendix A: Files created and modified (V7.1 → V7.2)
### Created (33)

- `agents/dashboard-intelligence-agent.md`
- `docs/17-v72-dashboard.md`
- `evals/dashboard-agent/case.yaml`
- `evals/dashboard-agent/fixture.sh`
- `evals/dashboard-agent/graders/answer-quality.md`
- `evals/dashboard-agent/graders/delegates-to-agent.md`
- `evals/dashboard-agent/prompt.md`
- `registry/manifests/dashboard-intelligence-agent.yaml`
- `schemas/dashboard.schema.json`
- `skills/artifact-dashboard-intelligence/SKILL.md`
- `skills/artifact-dashboard-intelligence/assets/command-center.core.js`
- `skills/artifact-dashboard-intelligence/assets/command-center.css`
- `skills/artifact-dashboard-intelligence/assets/command-center.template.html`
- `skills/artifact-dashboard-intelligence/assets/command-center.widgets.js`
- `scripts/render_dashboard.py`
- `skills/dashboard-intelligence/SKILL.md`
- `skills/dashboard-intelligence/references/dashboard-design-system.md`
- `skills/dashboard-intelligence/references/demo/sanofi_events_PUBLIC.json`
- `skills/dashboard-intelligence/references/demo/sanofi_financials_PUBLIC.json`
- `skills/dashboard-intelligence/references/metric-definitions.md`
- `skills/dashboard-intelligence/references/personas.yaml`
- `scripts/competitive_threads.py`
- `scripts/cross_domain_correlator.py`
- `scripts/dashboard_builder.py`
- `scripts/dashboard_state.py`
- `scripts/demo_provider.py`
- `scripts/domain_delta.py`
- `scripts/evidence_validator.py`
- `scripts/financial_intel.py`
- `scripts/marketing_signals.py`
- `scripts/memory_graph.py`
- `scripts/production_provider.py`
- `tests/run_dashboard.py`

### Modified (20)

- `.claude-plugin/plugin.json`
- `ARCHITECTURE.md`
- `CHANGELOG.md`
- `CONNECTORS.md`
- `README.md`
- `docs/00-index.md`
- `registry/agent-registry.json`
- `registry/manifests/account-intelligence-agent.yaml`
- `registry/manifests/competitive-thread-agent.yaml`
- `registry/manifests/financial-intelligence-agent.yaml`
- `registry/manifests/marketing-intelligence-agent.yaml`
- `registry/manifests/relationship-agent.yaml`
- `registry/skill-registry.json`
- `tests/README.md`
- `tests/run_agent_tests.sh`
- `agent_planner.py` (1 copies) → business-orchestrator
- `financial_intel.py` (2 copies) → business-orchestrator, financial-intelligence
- `marketing_signals.py` (2 copies) → business-orchestrator, marketing-intelligence

### Removed (0)

- none
