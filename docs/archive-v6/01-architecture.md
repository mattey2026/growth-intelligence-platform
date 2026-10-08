# 1. Architecture (v6.0)

```
 ANY DATA · ANY APPLICATION · ANY BUSINESS MODEL · ANY INDUSTRY · ANY SIZE
        │
 LAYER 0  business-context-discovery → Business Context Profile (persisted; reused unless contradicted)
        │
 MEMORY   business-memory: facts (temporal) · graph (nodes/edges) · ledger (predictions → decisions → actions → outcomes → learnings)
          · alerts (stateful) · sources (freshness) · summaries · preferences · run log (routing)
        │
 DELTA    delta_engine: recognize dataset → diff → re-analysis map → reuse unchanged conclusions
        │
 ROUTING  model_router: T0 code → T1 haiku → T2 sonnet → T3 opus → T4 fable (escalate on triggers only)
        │
 INTELLIGENCE  market-intelligence · data · knowledge · twin · orchestrator · BI copilot · win/loss · adaptive KPIs
        │
 DECISION & ACTION  growth engines + workflow skills; decisions in force; approval-gated actions
        │
 EXPERIENCE  executive-command-center (CEO / Investor / Owner) · daily briefing · business watch (stateful)
        │
 OUTCOME → LEARNING → UPDATED MEMORY GRAPH
```

## The loop
Every skill runs the 12 steps in `references/intelligence-loop.md`. The first question is always: **"Do I already know this, and has anything changed that would invalidate it?"**

## Components added in v6
| Kind | Component |
|---|---|
| Skills (4) | business-context-discovery · business-memory · market-intelligence · executive-command-center |
| Engines (7) | context_discovery · memory_graph · graph_build · delta_engine · model_router · kpi_engine · command_center |
| Subagents (4) | growth-light (haiku) · growth-analyst (sonnet) · growth-strategist (opus) · growth-expert (fable) |
| References | intelligence-loop · memory-model · model-routing (plus policy JSON) · adaptive-kpi-library · business-model-taxonomy · guardrails §17–19 |
