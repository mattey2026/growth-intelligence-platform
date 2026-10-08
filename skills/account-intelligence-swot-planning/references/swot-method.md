# Evidence-Based SWOT Method

## Scope
- **Strengths and weaknesses** are internal: *our* position in this account (relationships, footprint, adoption, delivery, contract position, satisfaction, capabilities, sponsorship).
- **Opportunities and threats** are external: the customer's strategy and situation, the market, competitors, regulation, and technology.

## Every item must have this chain

| Field | Content | Rule |
|---|---|---|
| `id` | S1…, W1…, O1…, T1… | Keep IDs stable across runs so change intelligence can track each item |
| `statement` | One sentence, specific to this account | Must fail the anti-generic test (below) |
| `evidence` | 1–3 cited facts (source, record, date; quote ≤ 25 words) | At least one internal or verifiable external source |
| `interpretation` | What the evidence means | Label it as an inference |
| `business_impact` | Revenue, retention, margin, or relationship consequence; quantified where possible | Show the formula if a number is given |
| `confidence` | High / Medium / Low | High requires two or more independent sources, or one system-of-record fact that is recent (≤ 90 days) |
| `recommended_response` | Leverage (S), fix (W), pursue (O), mitigate (T) | Link it to an action ID in the plan |
| `trend` | new / strengthened / weakened / unchanged vs the last snapshot | From change intelligence |

## Anti-generic test
Reject any item that:
1. would be true of most accounts ("strong relationship", "competitive market", "budget pressure" with no evidence);
2. has no cited evidence; or
3. cannot lead to a specific response.

Rejected items go to **Data gaps**, together with the data that would confirm or refute them.

## Checklists (prompts for looking, not templates to fill)
- **Strengths**: existing relationships, revenue footprint, adoption depth, differentiated capabilities in use, executive sponsorship, delivery performance (SLA, CSAT), contract position (term, renewal terms, switching cost), competitive advantages evidenced in wins.
- **Weaknesses**: relationship gaps (no economic buyer or executive coverage), low penetration vs peers, service problems, delivery issues, commercial pressure (discounting, disputes), poor stakeholder coverage, competitive disadvantages, contract limitations, data gaps, dependency on a single champion.
- **Opportunities**: whitespace (from `whitespace_matrix.py`), cross-sell, upsell, new business units and geographies, contract expansion, the customer's strategic initiatives, emerging needs, competitive displacement.
- **Threats**: competitor activity, cost pressure, churn signals, contract expiry, service deterioration, strategy changes, technology disruption, regulation, vendor consolidation, budget constraints.

## Example (good)
**T2 — Vendor consolidation threatens the analytics renewal**
- Evidence: CFO on the Q2 earnings call: "consolidating vendors by 30%" (transcript, 14 Aug); procurement asked for a price-benchmark RFI (email, 2 Sep).
- Interpretation: the analytics line ($420K ARR, renewal 31 Mar) is a likely consolidation target.
- Impact: $420K at risk.
- Confidence: High (two independent sources).
- Response: position a consolidated platform bundle; executive meeting with the CFO (action A3).

## Example (bad — rejected)
"The customer faces a competitive market." There is no evidence and no specific response, so it fails the anti-generic test.
