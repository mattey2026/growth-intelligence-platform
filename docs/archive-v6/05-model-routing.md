# 5. Model Routing

The full policy is in `references/model-routing.md` and `model-routing-policy.json`. The subagents are in `agents/`.

## Test: nine review tasks on Cowork
| Task | Tier | Binding |
|---|---|---|
| Recognize dataset · delta · KPI deltas · Monte Carlo · alert thresholds | T0 | Scripts (no model) |
| Extract stakeholder roles | T1 | growth-light (haiku) |
| Summarize A002 status from memory ($12.5M account) | T2 | growth-analyst (sonnet). No escalation: it is a summary, not a decision |
| Interpret A012 health change | T2 | growth-analyst (sonnet) |
| Recommend O010 pricing under a decision in force (conflict) | T3 | growth-strategist (opus) |
| Assess renewal risk for A002 ($12.5M) | T3 | Escalated on value at stake (an assessment) |
| Pricing question still unresolved after T3 | T4 | growth-expert (fable) |

## Surface limits (stated plainly)
| Surface | What routing means |
|---|---|
| Claude Code / Cowork | Real routing through plugin subagents (`model:` field). Cowork support is confirmed in Anthropic's help centre. Procedure: see docs/12 and `references/delegation-protocol.md` |
| API | Real routing through model IDs in your orchestrator |
| Claude.ai chat | Sub-agents are greyed out; no model switching. T0 steps still run as code, and the recommended tier is logged |
