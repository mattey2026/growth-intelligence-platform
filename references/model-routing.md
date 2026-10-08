# Model Routing (V7)

**V7:** a domain agent does the work; the tier chosen here is passed as the per-invocation `model` when the orchestrator delegates to it. The four tier agents are kept for generic work (v6.1 compatible). Every model call records tier, reason, estimated tokens, estimated cost, latency, confidence and escalation reason in the execution trace (`trace.py span`).

**Principle:** use the lowest-cost capable path. Deterministic code first; escalate only when a trigger fires.

| Tier | Use for | Claude Code / Cowork (plugin subagent) | API model ID | Claude.ai chat |
|---|---|---|---|---|
| **T0** deterministic | Aggregation, statistics, forecasts, financial maths, thresholds, deltas, KPI calculation, dataset recognition | Scripts, no model | — | Scripts |
| **T1** light | Classification, extraction, formatting, basic summaries, memory compression, simple anomaly labelling | `growth-light` (model: haiku) | claude-haiku-4-5-20251001 | Current model |
| **T2** standard | Analysis over retrieved context, account and deal reviews, drafting, status from memory | `growth-analyst` (model: sonnet) | claude-sonnet-5 | Current model |
| **T3** advanced | Strategy, cross-functional reasoning, scenarios, high-value decisions, executive decision support | `growth-strategist` (model: opus) | claude-opus-5-5 | Current model; recommend a strong model |
| **T4** expert | Highest-stakes questions still unresolved at T3; conflicting evidence | `growth-expert` (model: fable) | claude-fable-5-1 | Current model; flag for expert review |

## Escalation triggers (Cheap → Moderate → Advanced → Expert)
- Confidence below 0.6 after the current tier.
- Conflicting evidence across systems.
- Strategic, scenario, or decision scope.
- Value at stake above $1M, for **decisions and assessments only**. A status summary of a large account does not need a bigger model.
- Still unresolved after the current tier.

## Honest limits
- **Claude.ai chat:** a skill cannot switch models. The router still sends T0 work to code and logs the tier it *would* use.
- **Claude Code / Cowork:** routing is real, through the plugin's subagents. Anthropic's help centre confirms sub-agents run in Cowork and Claude Code, and appear greyed out in chat. Plugin subagents ignore the `hooks`, `mcpServers`, and `permissionMode` fields. An administrator setting `CLAUDE_CODE_SUBAGENT_MODEL_FORCE` overrides every agent's model; the run log records the intended tier regardless.
- **Procedure:** follow `delegation-protocol.md` (packet → Agent tool with the scoped name → wait → `reply_check.py` → escalate or accept → the main session writes memory).
- **API:** your orchestrator passes the model ID. Check current model availability and pricing in the Claude docs; this plugin does not hard-code prices.

## Transparency: log every major analysis
`memory_graph.py DB run-log RUN --tier T? --reason "…" --tokens N --escalated 0/1 --confidence C`

Report token figures as **estimates** unless actual usage data is available.
