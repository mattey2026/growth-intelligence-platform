# Adaptive KPI Library (v6.0)

The KPI framework is chosen by the Business Context Profile. `kpi_engine.py` computes only the KPIs the data supports, and lists each unsupported KPI with the input it needs.

| Model | Primary KPIs | Secondary | Typical data needed |
|---|---|---|---|
| **B2B** (incl. enterprise SaaS and services) | Contracted revenue / ARR, MRR, NRR, GRR, pipeline and weighted pipeline, coverage, win rate, ACV, gross margin, contribution, renewal exposure, concentration | CAC, LTV, CAC payback, sales cycle, slippage, cost to serve, discount leakage | Accounts, contracts, opportunities (with outcomes), finance, targets |
| **B2G** | Contract value, bid pipeline, award rate, renewal/recompete, procurement cycle, contract concentration, margin, revenue at risk | Protest rate, compliance findings | Bids, awards, contracts |
| **D2C** | Revenue, orders, AOV, conversion, CAC, ROAS, repeat purchase, returns, gross margin | LTV, subscription churn | Orders, sessions, ad spend |
| **B2C** | Revenue, active customers, AOV, frequency, retention, gross margin | NPS, returns | Transactions, customers |
| **B2B2C** | Sell-in, sell-through, partner concentration, end-customer demand | Channel inventory | Partner sales, POS |
| **Marketplace (C2C)** | GMV, take rate, active buyers and sellers, liquidity, repeat rate | Disputes | Listings, transactions |

## Views (executive-command-center)
| View | Focus |
|---|---|
| **CEO** | Growth, revenue, profitability, customers, pipeline, risk, market, opportunities |
| **Investor** | Growth, revenue quality (recurring share, concentration), margins, efficiency, retention, customer economics, cash, forecast |
| **Owner** | Revenue, profit, cash, customers, expenses, pipeline, risks, immediate actions |

## Rules
- Never show an unsupported KPI as zero or as an estimate.
- A metric that needs history (NRR, GRR, trends) becomes available after two snapshots in memory.
- Win rate requires at least 10 closed outcomes, including losses.
- Coverage requires a target.
