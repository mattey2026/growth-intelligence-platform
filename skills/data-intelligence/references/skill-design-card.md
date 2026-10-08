# Skill Design Card — data-intelligence (v4.0, 24-item standard)

| Item | Detail |
|---|---|
| Skill name | data-intelligence |
| Business problem | Data is fragmented, unmapped, duplicated, stale, and conflicting, so every analysis starts with manual wrangling |
| Persona | Everyone; RevOps and analysts as power users |
| Trigger | File uploaded; "analyze this"; a new source connected; a data-quality question |
| Inputs | Files, connectors, question |
| Data sources | Any source |
| Connectors / tools | Profiler, normalize, entity_resolver, ts_forecast, anomaly |
| Context requirements | Fiscal calendar, currency, stage ladder, definitions |
| Analytics | Profiling, KPIs, trends, segmentation, variance, correlation |
| Predictive | Period forecasts; anomalies |
| Reasoning | Infer field meaning; resolve identities; reconcile conflicts |
| Decision logic | System-of-record rules; confidence thresholds; blocking questions |
| Recommendations | Fixes, clean-up, next analyses |
| Actions | Clean files; approved write-back of hygiene fixes |
| Approval | Every write-back |
| Output | Data intelligence report + canonical files |
| Evidence | Lineage per row |
| Confidence | Mapping confidence; data-quality score |
| Error handling | Ambiguous dates, subtotals, merged headers → ask or exclude |
| Security | Masking; per-source permissions |
| Auditability | Mapping report + audit block |
| Baseline | Manual wrangling time; issues found manually |
| Success metrics | Time to insight −70%; issues caught; mapping accuracy |
| Test scenarios | Messy workbook; ambiguous dates; CRM↔ERP conflicts |
| Failure modes | Wrong mapping accepted; silent merges |
