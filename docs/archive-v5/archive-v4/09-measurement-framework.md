# 9. Measurement Framework

**Benchmark:** existing workflow vs Claude-assisted workflow. **No value is claimed merely because a skill works.** Details are in `references/measurement-framework.md`.

| Dimension | Metric | Baseline method | Claude-assisted method |
|---|---|---|---|
| Time saved | Minutes per task (prep, research, plan, review) | Time diary + observed sessions (2–4 weeks) | Telemetry + time diary |
| Administrative effort | Manual CRM updates, systems and screens touched | Observation, system logs | Approved change sets, tool calls |
| Interactions | Steps or clicks to reach a decision | Observation | Conversation turns |
| Accuracy | Error rate on audited outputs | Expert audit of manual outputs | Expert audit (blind) |
| Prediction accuracy | AUC, calibration, MAPE vs incumbent | Seller commit, CRM stage probability, manual forecast | Ledger |
| Recommendation quality | Acceptance rate; outcome of accepted vs not accepted | — | Ledger |
| Data completeness | Required fields populated and fresh | Profiler on system of record | Same, after the pilot |
| Decision latency | Signal → decision → action time | System timestamps | System timestamps |
| Adoption | Weekly active users, repeat use | — | Telemetry |
| Revenue, pipeline, customer impact | Win rate, slip rate, NRR/GRR, pipeline created | Matched control group, same period | Pilot group |
| Risk reduction | Risks flagged before materializing | Historical review | Ledger |
| ROI | (Measured value − cost) ÷ cost | — | Only differences against control |
