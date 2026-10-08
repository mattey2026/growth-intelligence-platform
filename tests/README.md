# Tests

| Suite | Command | Model calls | What it covers |
|---|---|---|---|
| **Starter prompts** | `python3 tests/run_prompts.py` | none (Chromium for 4 dashboard tests) | **263 tests**: per capability (34 each) coverage, quality, typed routing of primary prompts, routing with the capability hint (all prompts), follow-ups and slash commands; plus personas 19, context 5, contextual tier 5, discovery 9, dashboard 7, catalog sync 2, registry 2. Typed routing of *additional* prompts is reported, not asserted |
| **Dashboard suite** | `python3 tests/run_dashboard.py` | none (headless Chromium) | **83 tests**: skill 11, agent 10, contract 11, rendering 10, cross-filter 10, drill-down 10, persona 6, evidence 5, scenario 5, responsive/design 5. Browser tests are reported as SKIPPED (never passed) if Chromium is unavailable |
| **V7.1 suite** | `python3 tests/run_v71.py` | none | **104 tests** in 10 areas (below), including the Sanofi end-to-end test (D21), business-model adaptability (D22), and missing data (D23) |
| **V7 regression** | `python3 tests/run_offline.py` | none | 30 V7 scenarios plus 8 V6.1 regression checks |
| **Structure** | `python3 tests/validate_strict.py .` · `python3 scripts/registry.py . validate` · `claude plugin validate .` · `claude plugin validate ./agents` | none | YAML and frontmatter, registry consistency, official plugin schema |
| **Live evals** | `bash tests/run_agent_tests.sh` (step 4) | **yes** (your account) | 14 cases: 4 new in V7.1, 1 in V7.2 (`dashboard-agent`), 1 in V8 (`discovery`): `marketing-agent`, `financial-agent`, `competitive-thread-agent`, `sanofi-strategy-v71` |

## V7.1 areas
| Area | Tests | Spec minimum |
|---|---|---|
| MKT Marketing Intelligence | 11 | 10 |
| FIN Financial Intelligence | 13 | 10 |
| THR Competitive Threads | 19 | 16 |
| COR Growth Signal Correlation | 11 | 10 |
| ORC Orchestration | 8 | 5 |
| TWN Digital Twin | 5 | 5 |
| MEM Memory | 6 | 5 |
| EVG Evidence and Governance | 10 | 5 |
| OBS Observability | 3 | — |
| XF Cross-functional (D21 ×6, D15 ×2, D22 ×3, D23 ×7) | 18 | 10 |

## Fixtures (`tests/fixtures/`)
- `*_PUBLIC.json`: real, cited Sanofi figures and events (FY2024 and FY2025 results releases, the FY2025 results deck, and one secondary source for net debt).
- `*_SYNTHETIC.*`: invented internal data (contacts, marketing touches, competitor signals, contracts, B2C and B2B2C datasets). Every synthetic record's `source` says so.
- `growth_memory_v7.db`, workbooks, orders and customers: carried from V7.

Each run writes `tests/last-v71-run.json`. Delete it before packaging.
