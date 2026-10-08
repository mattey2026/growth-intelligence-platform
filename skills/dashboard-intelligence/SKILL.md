---
name: dashboard-intelligence
description: Dashboard Intelligence — decides what dashboard experience a user needs and produces a renderer-independent Dashboard Contract (schemas/dashboard.schema.json) — dashboard selection and composition, persona-adapted KPIs and visualizations, insights, anomalies, trends, cross-domain signals, drill-down paths, evidence, recommended actions, scenarios, comparisons, filters and state — with every number computed in code (T0) and nothing fabricated. Use when someone asks to "show my dashboard", "build a command center", "executive view", "account dashboard", "open the Sanofi dashboard", or when a dashboard needs data refreshed. Rendering is done by artifact-dashboard-intelligence.
---

# Dashboard Intelligence

Version 7.2 · Used by the **dashboard-intelligence-agent** and the Business Orchestrator (`dashboard` intent)

**Principle.** This skill defines the dashboard intelligence and design rules. The agent decides what experience the user needs. The **Dashboard Contract** standardizes the data. A renderer (first: the Claude Artifact in `artifact-dashboard-intelligence`) only displays it. Business logic never lives in the renderer.

## Pipeline
1. **Provider → bundle.**
   - `scripts/demo_provider.py`: demo inputs, run through the real V7.1 engines.
   - `scripts/production_provider.py`: Business Memory, CRM export, billing, P&L, operations, and filings.

   Both emit the same bundle. The production provider lists its `data_gaps` and never fills them.
2. **Builder → contract (T0).** `scripts/dashboard_builder.py --bundle b.json --persona <p> --role <r> --out contract.json --validate`
3. **Render.** `skills/artifact-dashboard-intelligence/scripts/render_dashboard.py --contract contract.json --out dashboard.html`, then publish it as an artifact.

## What this skill defines
| Capability | Where it is defined |
|---|---|
| **Dashboard selection** | The request maps to the Enterprise Growth Command Center (scope: account, portfolio or enterprise) and to the view that answers it (`queries[].ui_target`) |
| **Composition** | `layout.views`: widgets per tab; `pack()` makes every row sum to 12 columns |
| **KPI selection** | Persona KPI order (`references/personas.yaml`), limited to KPIs whose inputs exist |
| **Visualization selection** | Widget type per question: trend → line; value × probability → bubble radar; likelihood × impact → risk matrix; margin change → bridge; chronology → timeline; mix → bars; category × time → heatmap |
| **Persona adaptation** | Nine personas (Investor, CEO, CFO, COO, CRO, Growth Ops, Sales Head, Sales Director, AE). One contract carries `persona_layouts`; switching persona changes presentation only, never data access |
| **Metric definitions** | `references/metric-definitions.md` |
| **Insights and anomalies** | Trend-adjusted anomaly rule; four-quarter margin trend; cross-domain patterns P1–P5 as HYPOTHESIS |
| **Trend interpretation** | Direction and material change are computed; the narrative states only computed facts, each with evidence |
| **Cross-domain intelligence** | Uses the outputs of the financial, marketing, competitive-thread, correlator and delta engines |
| **Dashboard queries** | `queries[]`: suggested questions, each routed to the Business Orchestrator, with an optional UI target |
| **Drill-down** | `drill{}` graph (for example growth potential → driver → opportunity → evidence, signals, driver, competitive context, action). Every node has children or evidence, so there are no dead ends |
| **Evidence display** | `evidence[]`: source, date, observation, historical context, confidence, claim type, related signal, opportunity and decision |
| **Action recommendations** | `actions[]`: mapped to Action Center catalog actions with `approval_required`. The dashboard proposes; the Action Center executes after approval |
| **Scenario analysis** | `scenarios[]`: MODELED, with baseline, assumptions, scenario, delta and variants |
| **Filtering and cross-filtering** | `filters[]` plus facets on every object. KPIs carry precomputed `by_facet` values |
| **Comparison** | `comparisons{}`: eight modes, each only when its data exists; the rest are listed in `comparisons_unavailable` |
| **Dashboard state** | `state_defaults` in the contract; per-viewer state in browser storage; server-side state via `scripts/dashboard_state.py` (tenant-bound) |
| **Design system rules** | `references/dashboard-design-system.md` |

## Rules
- **Never fabricate.** Absent inputs produce "Not available", with what they need. Zero means zero, never unknown.
- **Security happens before rendering.** The role's data classes come from the tenant policy. Restricted data is *removed from the contract*, not hidden by the UI.
- **Consistency.** A figure shown in several widgets comes from one computation. Snapshot values are derived from the same series.
- **Demo labelling.** In demo mode every demo record says `DEMO DATA — NOT REAL CUSTOMER DATA`. Only cited public figures are real.

## Escalation and failure
- The builder validates the contract against the schema (`--validate`); a contract that fails validation is not rendered.
- Missing sections appear as explicit empty states.
- The dashboard agent works at T2. It escalates to T3 for strategic synthesis, and to T4 only for high-value executive synthesis.

## Examples
- "Show me my Sanofi dashboard." → demo or production provider → builder (persona from the user's role) → render → publish.
- "What's changed?" (with the dashboard open) → Ask Intelligence routes the question to the orchestrator and opens What changed.

<!-- starter-prompts:start (generated from growth-discovery catalog; do not edit) -->
## Starter prompts
Show these to users in business language; a chosen prompt goes to the Business Orchestrator. Full catalog and context-aware variants: growth-discovery.

**Dashboards** (/dashboard)
- Show me my growth command center.
- Show me what changed on the dashboard.
- Build the dashboard I need for this account.
- Show me opportunities and risks on the dashboard.
- Create an executive dashboard.
- Analyze this dashboard.
<!-- starter-prompts:end -->
