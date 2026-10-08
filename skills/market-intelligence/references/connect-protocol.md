# Connect Protocol (v3.0)

Connect is the first stage of every skill. Complete it before any analysis.

1. **Discover the sources.** List the connectors available in this session (CRM, ERP, ITSM, database or warehouse, spreadsheets, email, calendar, BI, documents, web) and any files the user has provided. Do not ask the user which application to open. Work out which sources the task needs.
2. **Plan the minimum sources** needed for the question. Least privilege: do not pull data the task does not need.
3. **Authorize each source separately.** Confirm that the user's own connector works for each source. If one fails, continue with the others and report the gap. Never infer access across systems.
4. **Profile before trusting.** For tabular data, run `scripts/data_profiler.py` (row counts, types, missing values, duplicates, outliers, candidate keys, date ranges).
5. **Normalize** to the canonical model (`semantic-model.md`) with `scripts/normalize.py` or explicit mapping. Show the mapping for any uncertain column and ask the user to confirm it if the result depends on it.
6. **Resolve identities** across sources, and report the match rate.
7. **Record lineage and coverage**: which sources were used, which were not, and the timestamp of each.

**Retrieve → Combine → Analyze → Predict → Recommend → Execute** is the tool chain. The value of each skill grows with every authorized source connected, and each skill should say which additional source would most improve its answer.
