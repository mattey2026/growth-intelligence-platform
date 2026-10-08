# Skill Design Card — rfp-response-composer (v3.0)

| # | Standard item | rfp-response-composer |
|---|---|---|
| 1 | Business problem | RFPs consume experts and create commitment risk |
| 2 | Target persona | Bid managers, presales |
| 3 | Data sources (canonical) | RFP, answer library, documents |
| 4 | Required tools/plugins | Document store, knowledge base |
| 5 | Inputs | RFP, content sources, deal context |
| 6 | Data preparation | Requirement parsing |
| 7 | Business logic | Compliance status rules |
| 8 | Analytics (descriptive/diagnostic) | Compliance matrix, gaps |
| 9 | Predictive analytics | Bid-win probability; effort |
| 10 | Reasoning | Only approved sources |
| 11 | Recommendations | Bid/no-bid; staffing |
| 12 | Actions | Drafts only |
| 13 | Human approval points | Expert, Legal, and pricing sign-off |
| 14 | Outputs | Matrix, drafts, risks |
| 15 | Success metrics | Hours per RFP; win rate |
| 16 | Baseline | Last 10 RFPs |
| 17 | Accuracy requirements | Effort MAPE; win calibration |
| 18 | Security requirements | Customer confidentiality |
| 19 | Failure modes | Invented capability claims |
| 20 | Test scenarios | Security questionnaire; FedRAMP refusal; liability flag |

The full test prompts are in `evals/evals.json` in the source repository.
