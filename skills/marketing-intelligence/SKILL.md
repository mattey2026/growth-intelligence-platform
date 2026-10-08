---
name: marketing-intelligence
description: Marketing Intelligence — turns raw marketing signals (email, web, webinars, events, intent data, executive briefings, campaigns) into account-level commercial intelligence — engagement change, executive engagement, buying-intent surges, campaign-to-account and campaign-to-opportunity influence (always labelled correlation unless tested), and evidence-backed commercial hypotheses — adapting to B2B accounts, B2C segments or B2B2C partners. Use for "what is marketing telling us", "is this account engaging", "which campaigns influenced this deal", "any buying intent", or when an account plan or opportunity needs marketing evidence.
---

# Marketing Intelligence

Version 7.1 · Used by the **marketing-intelligence-agent** (and the orchestrator, opportunity, and customer-growth flows)

## Operating instructions
1. **Load context.** The Business Context Profile gives the business model: B2B → accounts; B2C → segments; B2B2C → partners plus end-consumer demand. Recall the previous `AccountEngagement` from memory for the delta.
2. **Run the engine (T0):**
   `python scripts/marketing_signals.py --signals s.json [--contacts c.json] [--opportunities o.json] [--campaigns m.json] [--initiatives i.json] --model <B2B|B2C|B2B2C> --asof <date> --memory-db <db> --out mk.json`
3. **Interpret (T2).** Explain the material engagement changes, who is engaging (by role), and whether intent is surging. Only the hypotheses the engine produced may be presented as hypotheses.
4. **Hand off.** Pass the output to `growth-signal-orchestrator` (`cross_domain_correlator.py --marketing mk.json`) for pattern P1 and compound patterns.

## Input schema (signal)
`account_id` (or `segment` / `partner_id`), `occurred_at` (ISO), `type`, `source` are **required**. Optional: `signal_id, contact_id, contact_role, campaign_id, topic, channel`. Supporting files: contacts `{contact_id, role}`, opportunities `{opportunity_id, account_id, created_at, amount}`, campaigns `{campaign_id, name, experiment:{holdout_lift, source}}`, initiatives `{initiative_id, account_id, topic, source}`.

## Output schema (`mk.json`)
- `normalization`: received, normalized, duplicates_removed, rejected[], unclassified[].
- `units.<id>`:
  - `engagement_score`: current, previous, change_pct, direction, material, signals_current;
  - `executive_engagement`: current, previous, roles, evidence (null for B2C);
  - `buying_intent`: current, previous, surge, types, evidence;
  - `topics`, `negative_signals`, `sources`.
- `campaigns.<id>`: accounts, touches, `opportunities_influenced[]` (touches_before_creation, linear_touch_share, influenced_amount, claim_type, note).
- `hypotheses[]`: type, text, evidence, missing_evidence, confidence.
- `claims[]`: typed claims for the evidence validator.
- `memory`: what was stored.

## Signal taxonomy (`references/signal-taxonomy.md`)
| Category | Types |
|---|---|
| awareness | ad_impression, website_visit, social_engagement |
| engagement | email_open / click, content_download, webinar_register / attend, event_attend |
| intent | pricing_page_visit, demo_request, contact_sales, third_party_intent, competitor_comparison_view, rfp_download, trial_start, add_to_cart |
| conversion | purchase |
| executive | exec_meeting, exec_briefing_attend; plus any engagement or intent by a C-level, VP, or Head-of contact (B2B / B2B2C) |
| advocacy | reference_call, case_study_participation |
| negative | unsubscribe, email_bounce, complaint |

Synonyms are mapped. Unknown types are kept as `unclassified` (weight 0) and reported, never silently dropped.

## Confidence model
- **Engagement change** is material when the change is 25% or more and there are at least 3 signals, or when there are 3 or more signals in a new-engagement window.
- **Intent surge:** 3 or more intent signals and at least twice the previous window.
- **Hypothesis confidence:** 0.30 base, +0.15 for executive engagement, +0.15 for a matching initiative, +0.10 for a surge, +0.05 per intent signal (up to 3), capped at 0.8.
- **Campaign influence** is `CORRELATION`, and becomes `CAUSAL_ESTIMATE` only with a holdout result.

## Evidence requirements
Every claim cites signal ids or sources. Attribution never uses causal verbs ("drove", "caused") unless it is backed by an experiment. `evidence_validator.py claims` rejects unknown campaign or signal ids as fabricated activity.

## Memory behavior
Persists `MarketingSignal` (each normalized signal), `AccountEngagement` (per unit, per run), and `CampaignInfluence` (per campaign–opportunity pair), all tenant-scoped and queryable by account, time, and opportunity (`memory_graph.py obj-query`).

## Escalation rules
- Budget or attribution decisions, or influence over $1M → T3.
- Contradictory engagement data across sources → `ESCALATE`.
- Model confidence below 0.6 on a hypothesis presented to executives → label it Low, or escalate.

## Examples
- *"What is marketing telling us about BlueWave?"* → engagement down 40% with no executive touches → no expansion hypothesis; a risk note for the customer-growth flow.
- *"Which campaigns influenced O010?"* → M014 preceded opportunity creation (2 of 3 touches, a 0.67 share), reported as correlation.

## Failure handling
| Condition | Behaviour |
|---|---|
| No marketing data | Say so; the domain is reported as a data gap; confidence in dependent patterns is lowered |
| Unparseable dates or missing required fields | Record rejected with a reason |
| Aggregate-only data (no timestamps) | Report that change detection is impossible and why |

<!-- starter-prompts:start (generated from growth-discovery catalog; do not edit) -->
## Starter prompts
Show these to users in business language; a chosen prompt goes to the Business Orchestrator. Full catalog and context-aware variants: growth-discovery.

**Marketing Intelligence** (/marketing)
- Show me marketing activity affecting this account.
- Identify accounts showing buying intent.
- Show me marketing engagement trends.
- Which campaigns are influencing pipeline?
- Which accounts are warming?
- Show me marketing-to-revenue signals.
<!-- starter-prompts:end -->
