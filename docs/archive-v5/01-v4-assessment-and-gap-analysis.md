# 1–2. v4.0 Capability Assessment and Gap Analysis (with classification, deliverables 6–9)

## What v4.0 does well (kept)
- **Vendor-independent data layer**: profiler, normalize (10 entities), entity resolver.
- **Backtested, explainable predictions** with rules fallback and a ledger.
- **Deterministic analytics engines** (13 scripts, all tested).
- **Evidence discipline**: Data → Metric → Insight → Prediction → Recommendation → Action.
- **Governance**: per-system authorization, approval-gated actions, prompt-injection and tool-use controls.

## Structural problems found in the audit
| # | Problem | Evidence in v4 | v5 resolution |
|---|---|---|---|
| A | Three overlapping deal skills with circular references | deal-risk ↔ deal-strategy ↔ deal-intelligence all call each other | Consolidated into **deal-intelligence** (methods preserved as references) |
| B | Account context built three times, three contracts, no memory | account-360, the account strategist, and the meeting brief each assemble context; `account_360`, `account_state`, `account_health` | **Customer Digital Twin**: one persistent, time-aware model (`account_state` v2.0) |
| C | Signals ranked but never correlated | briefing `signal_ranker` scores independent signals | **Growth Signal Orchestrator** with a pattern library and contextual reasoning |
| D | No shared knowledge layer | RFP, deal desk, and competitive each read documents their own way | **Knowledge Intelligence** service |
| E | No learning loop from outcomes | Win/loss only on the roadmap | **Win/Loss Intelligence** feeding models, pricing, competitive, strategy |
| F | Sales-only scope | Nothing for marketing, product, partner, finance economics | New engines (P1/P2) plus cross-functional signals |
| G | "Why" questions unanswered | Descriptive analytics only per skill | **BI Copilot** with driver-tree decomposition |
| H | Pricing analytics would be misleading | Historical discount is confounded with deal risk | **Pricing Intelligence** with confounding detection and assumption ranges |
| I | Shared scripts copied into 16 skills | Each skill is self-contained by design | Kept for portability; single source in `platform/` of the source repo with a sync step |

## Classification of v4 skills
| v4 skill | Classification | v5 destination |
|---|---|---|
| data-intelligence | **Enhance** | Documents go to knowledge-intelligence; emits signals; "why" goes to BI copilot |
| deal-intelligence | **Enhance** (absorbs two) | Adds batch/audit mode, win/loss feature loop, pricing |
| deal-risk-intelligence | **Combine → Retire** | deal-intelligence batch mode + `deal-risk-method.md` |
| deal-strategy-win-plan | **Combine → Retire** | deal-intelligence + `deal-strategy-method.md` |
| pipeline-forecast-intelligence | **Enhance** | Win/loss calibration; "why" goes to the copilot |
| account-intelligence-swot-planning | **Enhance** | Twin-based; composed chain; account economics section |
| account-360-intelligence | **Replace → Platform** | customer-digital-twin |
| buying-committee-intelligence | **Enhance + rename** | relationship-intelligence (deal, account, portfolio) |
| deal-desk-precheck | **Enhance + rename** | pricing-intelligence (Deal Desk mode preserved) |
| renewal-expansion-radar | **Enhance (narrow)** | Retention focus; expansion goes to growth-opportunity-discovery |
| daily-growth-briefing | **Enhance** | Orchestrator patterns, watches, Next-Best-Account |
| scenario-planner | **Enhance** | Capacity scenarios ("+$100M") |
| meeting-intelligence-brief, meeting-follow-through | **Keep** | Read from and write to the twin via contracts |
| account-intel-outreach, rfp-response-composer | **Keep** | RFP answers from knowledge-intelligence |

**Result:** 16 skills (v4) → 21 skills (v5): 2 retired, 3 renamed and expanded, 7 new. The count grows only where a distinct capability was missing. Five of the seven new skills are platform services that every other skill reuses.

## Gap analysis vs the v5 brief
| Brief § | Capability | v4 | v5.0 |
|---|---|---|---|
| 3 | Growth Signal Orchestrator | Missing | **Built** (P0) |
| 4 | Customer Digital Twin | Partial (snapshots, no history) | **Built** (P0) |
| 5 | Growth Opportunity Discovery | Partial (whitespace only) | **Built** (P1) |
| 6 | Executive Relationship Intelligence | Partial (deal committee) | **Built** (P1) |
| 7 | Competitive Intelligence and Early Warning | Missing | **Built** (P1) |
| 8 | Win/Loss learning engine | Missing | **Built** (P0) |
| 9 | Next-Best-Account | Partial (prioritizer) | **Service** in briefing (P1) |
| 10 | Pricing Intelligence | Partial (deal desk) | **Built** (P1) |
| 11 | Account Economics | Missing | Interim section in account strategist; engine specified (P1) |
| 12 | Demand and Revenue Intelligence | Missing | Specified (P2) |
| 13 | Product Intelligence | Missing | Specified (P2) |
| 14 | Partner Intelligence | Missing | Specified (P2) |
| 15 | Sales Capacity Intelligence | Partial (scenarios) | Capacity scenarios built; analysis engine specified (P2) |
| 16 | Revenue Leakage | Missing | Specified (P2) |
| 17 | BI Copilot | Missing | **Built** (P0) |
| 18 | Business Watch | Missing | **Built** (P1) |
| 19 | Decision Intelligence | Missing | Specified (P1) |
| 20 | Knowledge Intelligence | Missing | **Built** (P0) |
| 21 | Growth Graph | Missing | Architecture designed (P3) |
