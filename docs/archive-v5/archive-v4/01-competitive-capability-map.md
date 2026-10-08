# 1. Competitive Capability Map: vs Salesforce Sales Cloud in Claude

**Baseline used.** The Sales Cloud plugin (1.0.0-beta.1.2, 32 skills) as shown in the Anthropic Directory listing. Its README describes the plugin as powered by the customer's Salesforce data, with Salesforce and Slack connected and optional email, calendar, productivity, and document connectors. The capability areas below are those named in our brief. We treat Sales Cloud as a **coverage baseline, not a blueprint**, and we make no claims about its internals beyond the listing.

**Architectural difference.** The baseline is anchored to one system of record. This platform is a **System of Intelligence + System of Action** above any system of record.

| Capability area | Baseline approach (as scoped) | This platform | Status | Differentiator # |
|---|---|---|---|---|
| Account context | Salesforce account data | `customer-digital-twin`: any CRM, ERP, ITSM, finance, files, web; identity resolution; conflict reporting | Built | 1, 2, 3 |
| Pipeline review | Salesforce pipeline | `pipeline-forecast-intelligence`: quality, aging, velocity, leakage, concentration, deal-level what-if | Built v4 | 4, 5, 11, 12 |
| Forecasting | Salesforce forecast data | P10/P50/P90 Monte Carlo on backtested deal probabilities; forecast-error tracking | Built | 5, 16 |
| Deal signals and deal review | Salesforce opportunity signals | `deal-intelligence`: Deal Review → Strategy → Close Plan → Execution, with backtested slip/win model and evidence scoring | Built v4 | 4, 5, 6 |
| Close plan | Present in baseline | Close plan derived from evidenced decision and paper process, predicted slippage, mutual-plan gaps | Built v4 | 5, 6 |
| Stakeholder mapping | Contact roles | Committee inferred from real interactions; strength scores; disengagement prediction | Built | 2, 5 |
| Account tiering | Present in baseline | `account_prioritizer.py`: configurable weights, drivers, rank stability | Built | 4 |
| Customer health | Present in baseline | Explained 9-dimension health; service, finance, and usage fused; churn propensity | Built | 2, 5, 7 |
| Expansion whitespace | Present in baseline | Peer-benchmarked potential, probability, and priority; refuses to size thin evidence | Built | 4, 5 |
| Renewals | Present in baseline | Notice-deadline-aware radar; revenue at risk; save plays | Built | 5, 6 |
| Prospect research and outreach | Present in baseline | Sourced point of view plus conversion propensity; drafts only | Built | 5 |
| Lead triage | Present in baseline | `lead-intelligence-triage` | Planned (Top 20 #16) | 5, 7 |
| Call prep and follow-up | Present in baseline | Cross-system brief with anomalies; follow-through with CRM reconciliation and the `deal_delta` evidence engine | Built | 2, 14 |
| Inbox management | Present in baseline | Folded into the Daily Growth Briefing (signal-ranked); dedicated skill planned | Partial | 13 |
| CRM hygiene | Present in baseline | `data-intelligence`: duplicates, stale records, cross-source conflicts, approval-gated write-back | Built v4 | 1, 2, 15 |
| Win/loss analysis | Present in baseline | `win-loss-intelligence` | Planned (Top 20 #15) | 4, 5 |
| — (beyond baseline) | — | Dynamic SWOT, strategic account plan, Account Change Intelligence | Built | 8, 9, 10 |
| — | — | Scenario and what-if modelling | Built | 11, 12 |
| — | — | Excel and file intelligence as first-class data | Built | 3 |
| — | — | Proactive Daily Growth Briefing | Built v4 | 13 |
| — | — | Cross-functional signal chain (Marketing → Finance) | Planned (#13) | 7 |
| — | — | Prediction ledger and outcome measurement | Built | 16 |

**Coverage gaps to close** (tracked in the roadmap): lead triage, win/loss, dedicated inbox triage, and executive command center.
