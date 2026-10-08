# Account Plan Framework

## 1. Current state
Revenue (trend, mix), products and services, contracts (value, term, renewal date, key clauses), relationships (coverage and strength), pipeline (value, stage, slip risk), health (risk dashboard), competitive position.

## 2. Desired future state
- **Revenue ambition** = current run-rate + growth trend (`ts_forecast.py`) + whitespace expected value (`whitespace_matrix.py`) + open pipeline × win probability. Show each component. Any stretch component above this is labelled a *stretch target*.
- Also state strategic objectives (3–5), target business units, target stakeholders, and expansion opportunities.

## 3. Growth strategy
Whitespace, cross-sell, upsell, new business, geography, product/service expansion, executive engagement. For each: rationale (the SWOT O-item ID), size, probability, and sequence.

## 4. Relationship strategy

| Role | Name | Strength 0–3 | Stance (evidence) | Our owner | Gap | Plan |
|---|---|---|---|---|---|---|

Roles to cover: economic buyer, decision maker, influencer, champion, blocker, procurement, technical, executive sponsor. Use `relationship-intelligence` for scoring.

## 5. Opportunity strategy (for each major opportunity)
Business problem · customer priority · value · competitive environment · decision process · key stakeholders · win strategy · risks · next actions · expected outcome (with slip and win probability from `deal-intelligence`).

## 6. Action plan schema (30/60/90 days)

| ID | Action | Owner/persona | Priority (P1–P3) | Due (30/60/90) | Expected impact | Dependencies | Required data | Required tools | Approval required | Success metric | Linked SWOT/risk |
|---|---|---|---|---|---|---|---|---|---|---|---|

Priority = impact (value at stake) × urgency (dates, risk level) × feasibility.

## 7. Portfolio prioritization defaults
Default criteria and weights (confirm with sales leadership):

| Criterion | Weight |
|---|---|
| Growth potential | 0.20 |
| Expansion propensity | 0.15 |
| Existing revenue | 0.10 |
| Whitespace | 0.10 |
| Strategic importance | 0.15 |
| Health | 0.10 |
| Relationship strength | 0.10 |
| Risk (lower is better) | 0.05 |
| Competitive position | 0.05 |

Use growth-weighted defaults for hunter teams, and retention-weighted defaults (raise health and risk) for farmer teams.
