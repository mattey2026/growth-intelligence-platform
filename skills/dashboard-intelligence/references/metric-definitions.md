# Metric definitions (T0, `dashboard_builder.py`)

All values are computed in code. A metric whose inputs are absent is **Not available**, with what it needs; it is never shown as zero.

| KPI | Definition | Needs |
|---|---|---|
| Revenue (TTM) | Σ last 12 months of account revenue; previous = the prior 12 months | 24 months of billing |
| Growth (qtr YoY) | Latest quarter ÷ same quarter a year earlier − 1; previous = the prior quarter's YoY | 6 quarters of account P&L |
| Pipeline | Σ value of open opportunities; previous from the prior snapshot | Opportunities |
| Forecast (weighted) | Σ value × CRM probability; previous uses the prior probabilities | Opportunities with probabilities |
| Account margin | Gross profit ÷ revenue, latest quarter | Quarterly account P&L and `financial_data` access |
| Growth potential | Σ incremental growth value (a renewal counts only its uplift) | Growth value per opportunity |
| New opportunities | Σ value of non-renewal opportunities | Opportunity categories |
| Value at risk | Σ value × (1 − probability) for opportunities contested by an active Medium or High threat thread | Competitive signals |
| Competitive exposure | Contested pipeline value ÷ pipeline | Competitive signals |

## Other rules

**Anomaly.** A month deviates from the trailing 6-month least-squares projection by at least 7%, **and** by at least 3× the residual scale (floored at 1% of the mean). Plain z-scores are not used, because they mislabel normal growth in smooth series.

**Health.** Eight dimensions, each 0–100, with **no composite**. A dimension without data shows "no data" and what it needs.

| Dimension | Formula |
|---|---|
| Financial | 70 + Δmargin(4q) × 1000 − ΔDSO(4q) × 2 |
| Customer | 100 × (CSAT − 1) ÷ 4 − 8 × open escalations |
| Relationship | Influence-weighted strength (Strong 0.9, Medium 0.6, Weak 0.3) |
| Marketing | 55 + min(35, engagement Δ points) |
| Competitive | 100 − 25 × high-risk threads − 10 × medium + 5 × open displacement opportunities |
| Commercial | 50 + 100 × (forecast ÷ pipeline − 0.4) + 20 × pipeline growth |
| Operational | 100 × SLA − 30 − 0.1 × (backlog − 100) |
| Strategic | 40 + 60 × impact-weighted pipeline share, × 0.8 unless compound pattern P5 is detected |

Status thresholds: ≥ 70 healthy, ≥ 45 watch, otherwise at risk. These are documented heuristics and are not calibrated on outcomes.

**Risks.** Each risk has a likelihood and an impact from 0 to 1:
- **Competitive:** likelihood = thread risk (High 0.75, Medium 0.5), +0.1 when accelerating; impact = contested value ÷ the largest opportunity.
- **Pipeline:** a probability drop of 5pp or more, or a close-date slip.
- **Financial:** margin compression, or DSO rising by more than 3 days over four quarters.
- **Customer:** CSAT falling, or a champion weakening.
- **Operational:** SLA falling.
- **Market:** an M&A event (a HYPOTHESIS, confidence 0.4).

**Scenarios.** All MODELED, with the assumptions stated in the output:
- **Renewal loss:** the annual contract value (value ÷ term) leaves the run rate, and dependent opportunities are lost with it.
- **Win:** the annual contract value is added.
- **Slip:** in-year weighted value moves out of the year.

**Changes.** From `domain_delta.py`: new, changed, deleted, corrected, contradictory. Confidence is 0.85, 0.80 when corrected, and 0.40 when contradictory.

**Displayed precision.** A change smaller than the displayed precision counts as flat, so a color never contradicts the number shown.
