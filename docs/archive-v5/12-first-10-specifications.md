# 23. Detailed Specifications: First 10 Capabilities (24-item standard)

Each skill's `references/skill-design-card.md` carries its own column.

| Item | **customer-digital-twin** | **growth-signal-orchestrator** | **business-intelligence-copilot** | **win-loss-intelligence** | **knowledge-intelligence** |
|---|---|---|---|---|---|
| Business problem | Account context rebuilt each time; no memory of change | Cross-functional signals are never connected | 'Why' questions take analysts days | Lessons from outcomes are lost | Wrong or stale document versions create risk |
| Persona | AMs, AEs, CSMs, executives; all account skills | Account teams, leaders, CS, RevOps | Executives, managers, RevOps, Finance | Sales leaders, RevOps, enablement, product marketing | Everyone; RFP, pricing, competitive skills |
| Trigger | Account 360, 'what changed and when', refresh schedule | Portfolio scan; twin changes; watches; 'connect the dots' | 'Why is X behind', 'what's driving' | Quarter close; 'why do we lose' | 'Latest policy', 'which document is right' |
| Inputs | Account id; sources; prior twin | Signals in window; custom patterns | Question; data | Closed deals; interviews | Question; repositories |
| Data sources | CRM, ERP, ITSM, usage, marketing, CLM, web | All producers via the signal bus | Any, via data-intelligence | CRM, transcripts, surveys | SharePoint, Confluence, Drive, KB, CLM |
| Connectors / tools | entity_resolver, twin_update, anomaly | signal_correlator | driver_tree, pipeline_whatif, winloss, ts_forecast | winloss_analyzer | knowledge_catalog |
| Context requirements | Hierarchy level; refresh cadence; store location | Pattern library; window | Plan definitions, hierarchy, fiscal calendar | Factor definitions | Status taxonomy; stale threshold |
| Analytics | Trends (slope per 30d), change log, tenure of current state | Pattern matching, function diversity | Variance, driver tree, price/volume bridge, cross-function tests | Rates with CIs, lift, p-values, drift, Pareto | Version groups, authority rank |
| Predictive | From owning skills (churn, expansion, slip) | Triggers churn, expansion, revenue at risk | Trajectory P10–P90 | Features for win and slip models | — |
| Reasoning | Causes stated as hypotheses; temporal order is not cause | Story, value at stake, hypotheses, alternative explanations | Test layered drivers; report unexplained remainder | Confounding and interaction checks | Content conflict comparison |
| Decision logic | System of record wins; append-only; confidence by snapshot count | min_matched, min_functions, strength | Stop when the gap is explained; quantify contributions | Reliable only if n ≥ 15 and p < 0.05; adoption only after backtest lift | Approved > published > draft; recency |
| Recommendations | 3–5 actions linked to changes | Intervention per function owner | 3–5 actions on controllable drivers | Motion, qualification, pricing, product changes | Archive, own, review |
| Actions | Snapshot write; hand-offs | Triggered skills; approved workflows | Hand to owning skills | Feed models; enablement drafts | Governance changes via the owner |
| Approval | First store configuration; all hand-off actions | Every workflow and action | Via the owning skills | Model feature adoption; process changes by the owning leader | Any document-store change |
| Output | Twin view | Pattern report | BI answer | Learning report | Answer with source |
| Evidence | Lineage per fact | Dated sequence with sources | Arithmetic shown; sources | Deal-level | Document, version, section |
| Confidence | Per trend and prediction | From the number of independent functions | Per driver | CI per pattern | Authority score |
| Error handling | Back-dating refused; first snapshot → no trends | Single-function data → state which sources are missing | Blocked function → layer marked untested | Low reason completeness → capped | No approved source → marked Unverified |
| Security | Internal-only stance; entitlement re-checked on read | Filter to entitled signals before correlating | Scoped to entitlement | No seller ranking | Repository ACLs; no cross-repository inference |
| Auditability | Snapshot history is itself the audit trail | Pattern ledger | bi_answer contract | winloss_learning contract | knowledge_answer |
| Baseline | Time to assemble context; surprises in reviews | Risk lead time; precision vs history | Analyst hours per question; decision latency | Model AUC; win rate | Time to authoritative answer; wrong-version incidents |
| Success metrics | −70% research; zero unexplained surprises | ≥ 60% precision; +4 weeks lead time | ≥ 90% audited-correct answers; −80% time | AUC lift; win-rate change vs control | −70% time; zero wrong-version customer answers |
| Test scenarios | 3 snapshots; back-date; blocked finance | ACME risk; GLOBEX opportunity; single signal → none | APAC gap; ambiguous plan; blocked finance | Planted effects recovered; confounded discount | Pricing v3 vs v4 draft; stale security paper |
| Failure modes | Stale sources; low identity match | Over-firing; spurious correlation | Parts not adding up; causal overreach | Spurious patterns; stale reasons | Blending conflicting facts |

| Item | **growth-opportunity-discovery** | **relationship-intelligence** | **competitive-intelligence** | **pricing-intelligence** | **business-watch** |
|---|---|---|---|---|---|
| Business problem | Growth found late and by chance | Relationship strength lives in sellers' heads | Competitive knowledge stale and anecdotal | Discount decisions on instinct; naive analytics misleading | Leaders can't watch every system |
| Persona | AEs, AMs, CSMs, leaders | AEs, AMs, executives, leaders | AEs, PMM, leaders | AEs, Deal Desk, Finance | Executives, managers, CS leaders |
| Trigger | 'Where can we grow'; expansion pattern | Stakeholders, coverage, sponsor change | Competitor mention; 'battlecard'; quarterly review | Discount question; quote check | 'Alert me when…' |
| Inputs | Install base; signals; research | Interactions; CRM contacts | Observations; win/loss; web | Deal economics; history | Watch definitions; state |
| Data sources | Twin, orchestrator, competitive, knowledge, web | Email, calendar, transcripts, CRM | CRM, transcripts, RFPs, web | CPQ, CRM, ERP | Twin, forecast, deal contracts |
| Connectors / tools | whitespace_matrix, opportunity_scorer, propensity | anomaly, propensity | competitive_watch, winloss_analyzer | pricing_model, anomaly | watch_evaluator |
| Context requirements | Catalogue, segments | Key-executive roles and weights | Strategic account list | Policy, cost, approval matrix | Thresholds; owners |
| Analytics | Peer benchmarks, adoption | Strength, trend, reciprocity, coverage score | Presence, win rates, trends | Realized price, discount anomalies | Condition evaluation |
| Predictive | Propensity per offering | Attrition, disengagement | Displacement probability | Win probability vs discount (identified or assumed) | Impact via investigation skills |
| Reasoning | Need and fit from evidence; timing windows | Verified departures only | Evidence-only strengths and weaknesses | Confounding detection; robustness | Investigate before notifying |
| Decision logic | EV × timing × competition × fit × evidence | Sponsor dependency, deterioration rules | Early-warning thresholds | Historical mode only if identified; else assumption range | Severity; false-fire tuning |
| Recommendations | Entry strategy and next action | Executive engagement and multi-threading plans | Responses per warning; deal plays | Non-price levers first; test | Next action per fired watch |
| Actions | Create opportunity, outreach drafts | Contact roles, meeting drafts | Enablement drafts | Deal Desk draft | Owner-approved channels |
| Approval | Opportunity creation; outreach | Contact changes; meeting requests | External-facing claims | All approvals remain human | Saving watches; channels; remediation |
| Output | Ranked opportunities | Relationship view | Competitive view | Pricing view | Watch results |
| Evidence | Signals plus need | Interaction evidence | Sourced, dated | Model mode shown | Previous → current values |
| Confidence | Evidenced vs hypothesis | Rule-based → model once labelled | Source diversity | Robust / not robust | From the investigating skill |
| Error handling | Thin peers → not sized | Silence ≠ departure | No price guessing | Confounded → assumption mode | Misconfigured → reported |
| Security | Research cited | Privacy stance; internal stance labels | Non-disparaging external use | Margin entitlement | Owner-scoped |
| Auditability | growth_opportunities | relationship_view | competitive_view | pricing_view, commercial_check | watch_results |
| Baseline | Opportunities per account; conversion | Coverage score; single-threaded share | Detection lead time | Leakage, margin, rework | Time from condition to action |
| Success metrics | More qualified pipeline vs control | Coverage +20 points; win rate by coverage | Earlier detection; competitive win rate | Margin up; rework −50% | −80% latency; <10% false fires |
| Test scenarios | M&A estimate ranks last | Sponsor departure; profiling refusal | CompX 8 new strategic accounts; CompY steady | 10→15% not robust; approval path | $6M slip fires, $1M doesn't; typo metric |
| Failure modes | Invented potential | Surveillance perception | Hearsay treated as fact | Causal overreach | Alert fatigue |
