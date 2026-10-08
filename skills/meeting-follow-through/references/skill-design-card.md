# Skill Design Card — meeting-follow-through (v3.0)

| # | Standard item | meeting-follow-through |
|---|---|---|
| 1 | Business problem | Meeting knowledge never reaches the system of record |
| 2 | Target persona | Account executives, account managers |
| 3 | Data sources (canonical) | Transcript or notes, opportunity, contacts |
| 4 | Required tools/plugins | Meeting platform, CRM, email |
| 5 | Inputs | Transcript, meeting metadata, CRM state |
| 6 | Data preparation | Account/opportunity matching; speaker and side attribution |
| 7 | Business logic | Evidence-or-blank; commitment test; reconciliation classes |
| 8 | Analytics (descriptive/diagnostic) | Change detection vs CRM |
| 9 | Predictive analytics | Commitment-miss risk; momentum shift |
| 10 | Reasoning | Buyer statements outweigh seller statements; contradictions surfaced |
| 11 | Recommendations | Follow-up cadence; escalation |
| 12 | Actions | CRM writes, email draft |
| 13 | Human approval points | Every write and email |
| 14 | Outputs | Change set, recap, deal_delta |
| 15 | Success metrics | Admin minutes; follow-up latency |
| 16 | Baseline | System timestamps for 8 weeks |
| 17 | Accuracy requirements | Proposal accuracy ≥ 90% |
| 18 | Security requirements | Consent check; field allowlist |
| 19 | Failure modes | Wrong match; invented commitments; rubber-stamping |
| 20 | Test scenarios | Discovery call; vague notes; internal-only meeting |

The full test prompts are in `evals/evals.json` in the source repository.
