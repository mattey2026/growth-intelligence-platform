# 10. Test Evidence: Two Reviews on the Test Workbook

| Step | Result | Status |
|---|---|---|
| Context discovery | B2B 0.98; Tech & IT Services hybrid (0.95); Enterprise (0.78) | ✅ |
| D2C and ambiguous counter-tests | D2C 0.47 → asks; Undetermined → asks | ✅ |
| Memory build (review 1) | 216 facts, 203 nodes, 355 edges, 16 sources, 10 ledger entries, 3 alerts | ✅ |
| Dataset recognition (review 2) | "Updated version of a known dataset, same schema"; profile reused | ✅ |
| Delta | 13 of 13 planted edits; 11 sheets reused | ✅ after fix |
| Conflict | A012 Healthy → Watch recorded as a transition | ✅ |
| Stateful alerts | UPDATE / SUPPRESS / FIRE_NEW as designed | ✅ |
| Outcome loop | O009: 0.83 → 1 (error +0.17); learning *proposed* | ✅ |
| Decision memory | CRO margin decision applied to the O010 recommendation | ✅ |
| Freshness | Marketing flagged stale (23 days) | ✅ after harness fix |
| Layered recall | L1 186 tokens vs raw 8,132 | ✅ |
| KPI deltas and forecast memory | Pipeline $54.8M → $52.8M reconciled; Q4 outlook $16.9M → $17.1M explained | ✅ after fix |
| Routing | 9 of 9 correct | ✅ after fixes |
| Compression | 24 points → 8; decision kept | ✅ |
| Command center | 3 views, 17 KPIs, 5 unsupported listed, desktop and mobile checked | ✅ after fixes |

## Defects found and fixed during testing (10)
1. pandas 3 string dtype meant categorical values were never read (industry "Undetermined").
2. Substring matching ("cto" inside "director") inflated the evidence.
3. D2C was not distinguished from B2C.
4. An empty-evidence case was labelled "B2B".
5. No graph nodes or edges were being built.
6. Composite keys were not detected, so Product_Usage changes were missed.
7. Closed-won deals were still counted as open pipeline.
8. Win rate would have been shown on n = 1.
9. Router: "summarize" matched "sum"; value-at-stake escalated summaries; a regex-escaping error.
10. Dashboard: serif font fallback; "+0.0%" noise.

**Test-harness issue (not an engine bug):** sources were not re-registered after the refresh. This became an explicit workflow step in data-intelligence.

## Limits of this test
- Synthetic data, with one simulated refresh.
- Both reviews ran on the same wall-clock day, so ledger timestamps use real time; deltas were queried by run ID.
- The decision and actions were **simulated** and labelled as such.
- Token figures are estimates.
- No live market research was included.

## v6.1 additions
- Official `claude plugin validate` passed on the plugin and its agents (Claude Code 2.1.284).
- A strict YAML validator was added, because the official validator tolerates `A: B` plain scalars.
- Delegation pipeline: packets built for T1–T3; `reply_check.py` correctly classified an OK reply, invented numbers (9 flagged), ESCALATE (next tier T3), and a contract break.
- **Memory correction demonstrated:** a v6 test entry had lost "$8" to shell expansion. It was fixed with a `correction` entry (history kept) that now travels in packets.
- **Eval-suite defect caught before shipping:** the expected weighted pipeline was wrong (8.97 → **8.72**).
- **Real agent runs still need your environment;** see docs/12.
