# 4. Delta-First and Token-Efficient Intelligence

1. **Recognize:** `delta_engine.py recognize new --memory-db db` classifies a dataset as new, an updated version of a known dataset, or schema-changed.
2. **Diff:** `delta_engine.py diff prev new` gives new, changed, and removed rows and cells, schema changes, and materiality. It supports single and composite keys.
3. **Decide:** if no material change, reuse the previous conclusions. Otherwise run a **partial re-analysis**: only the skills mapped to the changed sheets.
4. **Retrieve in layers:** L1 summary → L2 open items → L3 current facts and changes → L4 changed rows → L5 full analysis.

## Measured on the two-review test
| Measure | Value |
|---|---|
| Planted edits detected | **13 of 13** (after the composite-key fix) |
| Sheets reused vs re-analysed | **11 reused**, 5 re-analysed |
| Skills re-run | 10 (pricing, competitive, and outreach were not re-run: their data did not change) |
| A002 status from memory | L1 ≈ 186 tokens, L2 ≈ 469, L3 ≈ 1,035, vs the raw workbook ≈ 8,132 |
| Review context | ≈ 180k tokens (review 1, no memory) vs ≈ 22k (review 2, delta plus memory). **These are estimates from context sizes, not billing data.** |
