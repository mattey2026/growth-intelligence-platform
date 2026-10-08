# Measurement Framework (v6.0)

Every capability reports **Baseline → AI-assisted result → Delta → Business impact**, and business impact is claimed only when it shows up as a difference against a control group.

**Benchmark:** existing workflow vs Claude-assisted workflow. No value is claimed merely because a skill works.

Before deployment, every skill records a baseline for its metrics (listed in its `skill-design-card.md` under "Baseline").

| Dimension | Metric | How it is measured |
|---|---|---|
| Time saved | Minutes per task | Baseline time diary and observed sessions vs telemetry and diary |
| Admin effort | Manual updates, systems or screens used | Observation vs approved change sets and tool calls |
| Interactions | Steps to a decision | Observation vs conversation turns |
| Accuracy | Error rate | Blind expert audit of manual vs assisted outputs |
| Prediction accuracy | AUC, calibration, MAPE vs the incumbent method | Prediction ledger |
| Recommendation quality | Acceptance rate; outcomes when accepted vs when not | Prediction ledger |
| Data completeness | Required fields filled and fresh | Profiler before vs after |
| Decision latency | Time from signal to action | System timestamps |
| Adoption | Weekly active users; repeat use | Telemetry |
| Business impact | Win rate, slip, NRR/GRR, pipeline, margin | Matched control group, same period |
| ROI | (Measured value − cost) ÷ cost | Differences against control only |

Every output that proposes actions ends with the metric that will show whether the action worked.

## v6 efficiency metrics
| Metric | How it is measured |
|---|---|
| Tokens per answer | Run log (estimates unless measured) |
| Share of answers served from memory (L1–L3) vs full re-analysis | Run log |
| Sheets or sources reused vs re-analysed per refresh | delta_engine |
| Model-tier mix (T0–T4) and escalation rate | Run log |
| Alerts suppressed as non-material vs updates vs new | Alert state |
| Forecast error trend across reviews | Ledger: prediction → actual → error |
