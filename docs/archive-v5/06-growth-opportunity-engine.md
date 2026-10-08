# 13. Growth Opportunity Engine: Design

**Signal + Customer Need + Fit + Timing + Probability + Commercial Potential**

| Stage | Design |
|---|---|
| Candidate generators | Whitespace and peer benchmark (`whitespace_matrix`); utilization and adoption (twin); orchestrator patterns (expansion readiness, service-driven); competitive (expiring competitor contracts); external research (M&A, regulation, technology programmes, investment); product usage (new use cases) |
| Evidence | Each component needs dated, sourced evidence; offering fit via knowledge-intelligence |
| Sizing | Potential: quote > peer median > estimate. Probability: propensity model > base rate > judgment. Each basis is shown |
| Scoring | `opportunity_scorer.py`: EV = potential × probability; priority = EV × timing × competition × fit × evidence × low-evidence penalty; ROI vs required investment; status evidenced or hypothesis |
| Entry strategy | Stakeholder path (relationship-intelligence), value hypothesis, proof points, competitive approach, next action |
| Learning | Conversion by type and by probability basis → recalibration |

**Tested behaviour:** a $1.5M M&A idea resting on an estimate and a judgment ranks below evidenced $250K–$900K opportunities, flagged as a hypothesis.
