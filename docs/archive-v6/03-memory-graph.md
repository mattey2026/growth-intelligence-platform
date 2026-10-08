# 3. Business Memory Graph

The full schema is in `references/memory-model.md`. The store is one portable SQLite file.

| Spec requirement | Implementation |
|---|---|
| Graph of Business → … → Outcome | `graph_build.py` + `graph-upsert`; `neighbors` traversal. Test: 203 nodes, 355 edges |
| Memory ≠ chat history | Facts, ledger, and summaries, not transcripts |
| Temporal memory | first/last observed, previous value, change, rate per 30 days, status, confidence, source |
| Conflict resolution | Categorical belief changes are recorded as `conflict` (previous belief → new evidence → resolution). Test: A012 Healthy → Watch |
| Summarization | `summary-write` per entity and run; read first by later analyses |
| Compression | Keeps current state plus the last N values; folds the rest; never removes decisions, outcomes, learnings, or alerts. Test: 24 points → 8 |
| Decision memory | `record decision …`; `decisions --scope`; guardrails §19 |
| Preference memory | `pref-set`, only when set explicitly |
| Data-source memory | `source-register` with schema hash and refresh history; `sources-check` flags stale sources |
| Quality control | Each item has source, timestamp, confidence, and status (confirmed / inferred / historical / stale / contradicted / unknown) |
| Persistence | Claude Code / Cowork: project folder. Claude.ai chat: user's Drive or re-upload (the sandbox resets). Enterprise: warehouse tables |
