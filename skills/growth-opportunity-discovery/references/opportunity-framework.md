# Opportunity Framework

## Evaluation: Signal + Need + Fit + Timing + Probability + Potential

| Component | Evidence required | Weak (flag) |
|---|---|---|
| Signal | Dated, sourced event or trend | Undated or "general market" |
| Need | Customer's words, initiative, measurable problem | Assumed need |
| Fit | Offering capability matches the need (knowledge-intelligence) | Unverified capability |
| Timing | Budget cycle, expiry date, initiative start | No date |
| Probability | Propensity model > base rate > judgment | Judgment |
| Potential | Quote > peer median > estimate | Estimate |

## Formulas
- Expected value = potential × probability.
- Priority = EV × timing factor × competition factor × fit factor × evidence factor × low-evidence penalty. See `opportunity_scorer.py` for the constants.

## Status
- **Evidenced**: 2 or more independent pieces of evidence (signals plus need).
- **Hypothesis**: fewer than 2. Shown only with the specific evidence that would confirm it.
