---
name: artifact-dashboard-intelligence
description: Artifact Dashboard renderer — turns a Dashboard Contract (schemas/dashboard.schema.json) into the Enterprise Growth Command Center, an interactive, self-contained Claude Artifact in the Growth Intelligence Design System (light/dark, 12-column grid, KPI strip, state of the business, what changed, trends, growth drivers, opportunity radar, risk matrix, competitive threads and timeline, financial, marketing, relationship map, SWOT, health, actions, scenario lab, comparisons, drill-down, evidence drawer, cross-filtering, Ask Intelligence). Use after dashboard-intelligence has built a contract, when the user wants to see or publish the dashboard. Contains no business logic.
---

> Shared scripts and references live at the plugin root: `../../scripts/` and `../../references/` from this skill's folder.


# Artifact Dashboard Intelligence (renderer)

Version 7.2 · The first renderer for the Dashboard Contract. React, Next.js, portal or mobile renderers can replace it without touching the intelligence layer.

## Use
```
python ../../scripts/render_dashboard.py --contract contract.json --out /mnt/user-data/outputs/<entity>-command-center.html
```
Then publish it with the Artifact tool. The script validates the contract against the schema and refuses to render an invalid one.

## Assets
| Asset | Contents |
|---|---|
| `command-center.template.html` | Shell with the contract slot |
| `command-center.css` | Design-system tokens and components |
| `command-center.core.js` | State, cross-filter, drawers, drill-down, evidence, Ask Intelligence |
| `command-center.widgets.js` | 23 widget types and the page frame |

## Renderer rules
1. **No business logic.** No scoring, financial calculation, business rules, competitive reasoning or recommendations. Every value, delta, label, sentiment and classification comes from the contract. The only arithmetic is presentation: chart pixel scales and sorting on provided values.
2. **Cross-filtering** matches facets that the contract supplies. KPIs switch to precomputed `by_facet` values, or show that they are not split by that dimension. Unrelated items are dimmed; mismatched items are hidden.
3. **Ask Intelligence** never reasons locally. It (a) navigates or filters the UI when a question maps to a known view, and (b) hands the question, with dashboard context, to the **Business Orchestrator**: through `sendPrompt` where available, otherwise by copying it for the chat.
4. **Actions** show "Request approval" and "Send to Action Center". They route through the orchestrator and the Action Center, and never execute from the page.
5. **State** (persona, view, filters, time range, theme, density, saved views) is kept per viewer in browser storage, keyed by tenant, dashboard and entity. It is wrapped in try/catch and falls back to defaults.
6. **Published-page constraints.** Self-contained. Only Google Fonts load externally, with a system fallback. Safe-area insets. Light and dark themes.

## Views
Overview · Growth · Accounts · Pipeline · Customers · Competition · Market · Financial · Marketing · Operations · Decisions · Actions. Which views appear depends on the persona and the role's permissions.
