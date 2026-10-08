# Agent Control Plane (V7)

```
USER → Intent Understanding (A) → Business Context (B) → Memory Retrieval (C) → Delta (D) → Agent Planner (E)
     → Agent Registry (F) / Agent Router (G) / Skill Router (H) / Tool Router (I) / Model Router (J)
     → Execution Manager (K) → Evidence Validator (L) → Policy Gate (M) → Human Approval (N) → Action Manager (O)
     → Outcome Tracker (P) → Learning Manager (Q) → Memory Update   ⟂ Observability (R) across every step
```

| # | Component | Implementation | Status |
|---|---|---|---|
| A | Intent Understanding | `agent_planner.py` (22 intents, 6 modes, entities, value, horizon, role) plus LLM refinement by the orchestrator | IMPLEMENTED (rules) + PARTIAL (LLM refinement is instruction-driven) |
| B | Business Context Engine | `context_discovery.py` + profile in memory | IMPLEMENTED (v6) |
| C | Memory Retrieval | `memory_graph.py recall` L1–L3; `handoff_packet.py` | IMPLEMENTED |
| D | Delta Intelligence | `delta_engine.py`, `memory_graph.py delta`; planner memory-reuse short-circuit | IMPLEMENTED |
| E | Agent Planner | `agent_planner.py`: step graph, agents, skills, data, tools, tier, parallel groups, approvals, conditional T4, relative cost | IMPLEMENTED |
| F | Agent Registry | `registry/manifests/*.yaml`, `registry.py` (validate / build / list / can / set-status), `registry/agent-registry.json` | IMPLEMENTED |
| G | Agent Router | The planner assigns agents per step; the orchestrator calls the Agent tool with the scoped name | IMPLEMENTED (plan) / runtime depends on the surface |
| H | Skill Router | Skills are bound per agent via manifest `allowed_skills` + `skills:` preload; the skill description drives invocation | IMPLEMENTED |
| I | Tool Router | Manifest `allowed_tools` → generated agent `tools` / `disallowedTools`; T0 steps name their scripts | IMPLEMENTED |
| J | Model Router | `model_router.py` + per-invocation `model` override on the Agent tool | IMPLEMENTED (Claude Code / Cowork); logged-only in chat |
| K | Execution Manager | Orchestrator procedure (dependency order, parallel groups, background completion) | PARTIAL: instruction-driven, not a separate runtime |
| L | Evidence Validator | `evidence_validator.py` (contract, provenance, external facts, fact vs inference, decisions, injection, cross-agent conflicts) | IMPLEMENTED |
| M | Policy / Governance Gate | `policy_gate.py` + `policy/action-catalog.yaml` + tenant policy | IMPLEMENTED |
| N | Human Approval Gate | `policy_gate` REQUIRE_APPROVAL + `action_manager` approve / reject (owner-checked) | IMPLEMENTED (approval collected in conversation) |
| O | Action Manager | `action_manager.py` (enforced lifecycle and audit) | IMPLEMENTED (execution via the user's connectors) |
| P | Outcome Tracker | `action_manager outcome`, `memory_graph outcome` (prediction → actual → error) | IMPLEMENTED |
| Q | Learning Manager | `learning_manager.py` (candidate → validated → adopted rule, versioned, approver required) | IMPLEMENTED |
| R | Observability | `trace.py` (spans, cost, latency, summary, admin HTML) | IMPLEMENTED; token counts are estimates unless measured |
