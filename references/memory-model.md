# Memory Model (v6.0)

## Store
One SQLite file (`growth_memory.db`), managed by `scripts/memory_graph.py`. The schema is portable to any warehouse (same tables).

| Table | Holds |
|---|---|
| profile | Business Context Profile (one row) |
| facts | Temporal facts: entity, attribute, value, observed_at, first_observed, prev_value, change, rate per 30 days, status, confidence, source, last_verified, is_current |
| nodes / edges | Memory Graph: Business → Industry → Customer/Account → Person → Product → Opportunity → Contract → Case → Competitor … with first/last observed and status |
| ledger | analysis · prediction · recommendation · decision · action · approval · exception · assumption · scenario · correction · observation · outcome · learning · conflict |
| alerts | Stateful alerts: open / acknowledged / resolved; last values; times fired |
| sources | Data-source memory: schema hash, columns, rows, last refresh, freshness limit, quality, limitations, refresh history |
| runs | Analysis log with model-routing metadata |
| summaries | Compact memory artifacts per entity and run |
| prefs | Preferences explicitly set by the user |

## Memory node (conceptual view)
```
Entity: A002 · Observation: Core adoption 44 → 38 (−12.9 points/30d) · Date: 2026-10-13 · Evidence: Product_Usage
Previous prediction: renewal ~0.60 (High risk) · Recommended: CIO incident review · Decision: — · Action: CIO meeting planned 8 Oct
Outcome: pending (meeting result not recorded) · Next review: 2026-10-20
```
Assemble this view from `recall <entity> --level 2/3`.

## Status vocabulary
**Confirmed** (observed in a source) · **Inferred** (derived by analysis) · **Historical** (superseded) · **Stale** (not re-verified within its freshness window) · **Contradicted** (inferred belief overturned by evidence) · **Unknown**

## Temporal rules
- Every fact records first observed, last observed, current and previous values, change, rate, trend, confidence, source, and timestamp.
- New evidence never overwrites silently. The old value becomes *historical*. For categorical beliefs (health, risk tier, business model), a **conflict** entry records: previous belief → new evidence → resolution.

## Layered retrieval (token efficiency)
L1 summary (~200 tokens) → L2 open items (~500) → L3 current facts and changes (~1,000) → L4 changed source rows → L5 full analysis. Measured on the test workbook: L1 is about 2% of the raw data, L3 about 13%. The savings grow with data size.

## Compression
`compress --keep-history N --stale-days D`:
- keep the current state plus the last N values per attribute;
- fold older values into a compressed record (count, min, max);
- mark facts not re-verified within D days as stale.

**Never compress:** decisions, outcomes, learnings, alerts, source history.

## Persistence by surface
| Surface | How memory persists |
|---|---|
| Claude Code / Cowork | The file lives in the project folder and persists between sessions |
| Claude.ai chat | The sandbox resets. Save to Drive (connector) or return the file to the user; load it at the start of the next session. If the file is missing, say memory is unavailable. **Never imply remembered state that was not loaded.** |
| Enterprise / API | Mirror the tables in the data platform; the skills read and write through the SQL connector |

## Governance
Memory stores only data the writing user is entitled to see, and entitlement is re-checked on read. Retention follows policy. Deleting a source's data deletes the derived facts. Personal data is minimized (business roles, not personal lives). See guardrails §17.

## V7.1 additions
**Typed domain objects** (table `domain_objects`; `memory_graph.py obj-put` / `obj-query`):
- MarketingSignal, AccountEngagement, CampaignInfluence;
- FinancialMetric, FinancialSignal;
- CompetitiveEvent, CompetitiveThread, CompetitiveHypothesis, CompetitiveOutcome;
- CrossDomainPattern.

Each object carries obj_type, tenant, account_id, competitor_id, opportunity_id, observed_at, recorded_at, source, source_date, confidence, claim_type, and data. Objects are queryable by account, competitor, opportunity, and time, and only within the bound tenant.

**Competitive threads** (tables `competitive_threads` and `thread_signals`, maintained by `competitive_threads.py`) persist across sessions. Their schema is in `skills/competitive-thread-intelligence/SKILL.md`.

**Twin snapshots** (table `twin_snapshots`) hold the eight state domains. FORECAST, WHAT_IF, and TARGET live in the ledger as `scenario` rows.
