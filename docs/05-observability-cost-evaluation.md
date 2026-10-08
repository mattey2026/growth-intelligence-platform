# 5. Observability, Cost, and Evaluation

## Execution trace (`trace.py`)
Every request produces spans for: request, intent, context, plan, step, model_call, tool, evidence, decision, action, approval, error, escalation, outcome, and answer. Each span records agent, tier, skills, data, tools, tokens (estimated unless measured), cost, latency, confidence, and escalation.
- `trace.py summary` gives: cost per query, per agent, per recommendation, and per successful action; tier mix; escalations; errors; latency.
- `trace.py html` produces the admin observability view.

## Cost
Costs are in **relative units** (T0 0 · T1 1 · T2 4 · T3 12 · T4 20 per 1k tokens) until an administrator adds `policy/price-table.yaml` with current prices from Anthropic's pricing documentation. The package does not hard-code prices.

Cost levers that are implemented:
- memory reuse (the test showed a 4-step plan at 2.4 units vs 10 for the full plan);
- delta-only re-analysis;
- T0 code for all arithmetic;
- lowest capable tier, with T4 conditional only;
- parallel groups;
- limited skill preloads;
- compact packets.

## Evaluation framework
| Layer | What | Where |
|---|---|---|
| Offline suite | 30 V7 scenarios (deterministic parts) + V6.1 regression | `tests/run_offline.py` (30/30 + 8/8 at release) |
| Live agent evals | 8 `claude plugin eval` cases: delegation (5, from v6.1), Sanofi growth, prompt injection, challenge mode | `evals/` |
| Structural | `claude plugin validate`, strict YAML, `registry.py validate` | `tests/run_agent_tests.sh` |
| Per-agent metrics (accuracy, evidence quality, hallucination rate, calibration, usefulness, action success, prediction accuracy, acceptance, time saved, cost, impact) | Defined in `references/measurement-framework.md`; scores are written to the manifest `evaluation.score` | DESIGNED (scoring pipeline not automated) |
