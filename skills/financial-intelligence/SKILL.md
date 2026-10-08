---
name: financial-intelligence
description: Financial Intelligence — analyzes an account's or the business's financials (revenue, growth, margins, EBITDA, cash flow, capex, debt, cash, working capital, DSO, business-unit and geographic performance, investment, M&A, restructuring, cost pressure, technology investment), computing every metric deterministically in code with source, date and confidence, never fabricating missing values, and translating financial signals into commercial implications. Use for "show me the financial story", "how is this company doing financially", "margin trend", "can they fund this", "what do their results mean for us", or when an account plan, opportunity or decision needs financial evidence.
---

> Shared scripts and references live at the plugin root: `../../scripts/` and `../../references/` from this skill's folder.


# Financial Intelligence

Version 7.1 · Used by the **financial-intelligence-agent** (and account, opportunity, orchestrator, and decision flows)

## Operating instructions
1. **Collect sourced facts.** Use public filings and results releases (Research agent: WebSearch/WebFetch, cited) or internal finance data. Write them as long-format facts, each with `source`, `source_date`, and `basis` (reported / non_gaap / secondary / estimate).
2. **Compute (T0; never in the LLM):**
   `python ../../scripts/financial_intel.py --facts f.json [--events e.json] --model <B2B|B2C|B2B2C> [--public] --memory-db <db> --out fi.json`
3. **Interpret (T2; T3 for strategic implications).** Tell the financial story from `metrics`, `trends`, `material_changes`, and `signals`. Present `commercial_implications` as **hypotheses**.
4. **Hand off.** Pass the output to `growth-signal-orchestrator` (patterns P2 and P3), `growth-opportunity-discovery`, `account-intelligence-swot-planning` (section 2), and `decision-intelligence`.

## Input schema
- **Facts:** `{entity, period, metric, value, unit, currency, source, source_date, basis[, segment: "bu:<name>"|"geo:<name>"]}`.
- **Metrics:** revenue, gross_profit, operating_income, ebitda, d_and_a, net_income, operating_cash_flow, capex, free_cash_flow, cash, total_debt, net_debt, current_assets, current_liabilities, accounts_receivable, rd_expense, sga_expense, tech_investment, headcount.
- **Events:** `{entity, date, type: m_and_a|restructuring|investment|divestiture|cost_program|guidance, text, source, source_date}`.

## Output schema (`fi.json`)
- `metrics[period][metric]`: value, unit, formula, claim_type (FACT for reported, DERIVED for calculated), inputs with provenance, confidence (the minimum of its inputs).
- `missing[period]`: each metric, with the inputs it needs.
- `trends` (including CAGR) and `material_changes`.
- `signals[]`: kind, text, evidence, confidence, claim_type.
- `commercial_implications[]` (HYPOTHESIS), `sensitivity`, `data_quality`, `memory`.

## Deterministic rules (never fabricate)
| Metric | Rule |
|---|---|
| EBITDA | Reported, or operating income + D&A. **Never** derived from ratios or leverage multiples |
| FCF | Reported, or OCF − capex |
| Net debt | Reported, or debt − cash |
| DSO | AR ÷ revenue × 365 |
| Working capital | Current assets − current liabilities |

- An `estimate` basis is excluded from facts.
- Secondary sources (for example press summaries) get confidence 0.7 and are listed in `data_quality`.

## Signals
margin_pressure / margin_expansion (≥1pp) · revenue_decline · growth_acceleration (≥3pp) · cost_pressure / operating_leverage (opex growth vs revenue growth ±1pp) · cash_generation_improving / weakening (FCF ±20%) · investment_reduction · technology_investment · m_and_a · restructuring · cost_transformation · divestiture · guidance.

## Confidence model
- Metric confidence is the minimum of its inputs' confidence: reported 0.95, non-GAAP 0.9, secondary 0.7.
- Signal confidence is 0.75–0.9 for computed signals, 0.9 for sourced events, and 0.4 for unsourced events.
- Implication confidence is signal confidence × 0.7, because an implication is an inference.

## Evidence and sensitivity
- Every number traces to a source fact or a stated formula. `evidence_validator.py claims` rejects financial values that are not in the source facts.
- Data is tagged `public_financials` (with `--public`) or `financial_confidential`. The policy gate requires `financial_data` access plus the `financial_confidential` clearance for non-public financials.

## Memory behavior
Persists `FinancialMetric` (per period and metric, with formula and sensitivity) and `FinancialSignal`, both queryable by account and time.

## Escalation rules
- M&A, restructuring, or decisions of $5M or more → T3.
- Sources that disagree on the same metric and period → `ESCALATE` with both values.
- Only secondary sources for a key metric → report Low confidence.

## Examples
- *"Show me Sanofi's financial story."* FY2025 revenue growth 6.2%, gross margin 77.5%, business operating margin 27.8%, FCF margin 18.5%. EBITDA, capex, DSO, and cash are **missing** from the sources used. Signals: margin expansion, operating leverage, improving cash generation, the pending Dynavax acquisition, and 2026 guidance.

## Failure handling
| Condition | Behaviour |
|---|---|
| No financial data | The domain is reported as a data gap and dependent patterns are marked emerging or not detected; ask for filings or finance access |
| Single period | No trends; metrics only |
| Conflicting sources | Both are kept; the conflict is flagged |

<!-- starter-prompts:start (generated from growth-discovery catalog; do not edit) -->
## Starter prompts
Show these to users in business language; a chosen prompt goes to the Business Orchestrator. Full catalog and context-aware variants: growth-discovery.

**Financial Intelligence** (/financial)
- Show me the financial story.
- Analyze the last five years of financials.
- What financial changes matter?
- Show me margin and profitability trends.
- Find financial signals that could create opportunities.
- Explain the financial position.
<!-- starter-prompts:end -->
