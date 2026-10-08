# Watch Library (starting definitions)

| Watch | entity_type | metric | condition | Default |
|---|---|---|---|---|
| Strategic account health drops > 20% | account (tier = strategic) | health_score | pct_change ≤ | −20 |
| Deal > $5M slips | opportunity (min_amount) | close_date | moved_later | 5,000,000 |
| Forecast below threshold | forecast | P50 | value < | the user's threshold |
| Pipeline coverage below target | forecast | coverage_ratio | value < | 3.0 |
| Competitor enters strategic account | account (strategic) | competitor_new | event | — |
| Expansion probability exceeds threshold | account | expansion_probability | crossed | 0.6 |
| Revenue at risk exceeds threshold | account or portfolio | revenue_at_risk | value > | the user's threshold |
| Customer sentiment deteriorates | account | sentiment_index | pct_change ≤ | −15 |
| Executive sponsor leaves | account | sponsor_departed | event | — |

The metrics come from the twin (`account_state` v2.0), forecast_view, and deal_intelligence contracts.
