# 1. Architecture

```
USER → INTERACTION (ASK · PREPARE · INVESTIGATE · WATCH · DECIDE · ACT)
  → BUSINESS ORCHESTRATOR (main session; skill: business-orchestrator)
  → AGENT PLANNER (agent_planner.py)
  → BUSINESS CONTEXT (context_discovery) → MEMORY + DIGITAL TWIN (memory_graph, twin_state) → DELTA (delta_engine)
  → DOMAIN AGENTS (17 plugin agents, least privilege) → SKILLS (30) → DATA / TOOLS (connectors, scripts) → ANALYTICS (T0 scripts)
  → MODEL ROUTER (model_router; the tier is passed as the per-invocation model) → REASONING TIERS T1–T4
  → EVIDENCE VALIDATION (evidence_validator) → DECISION INTELLIGENCE (decision_record)
  → GOVERNANCE (policy_gate + governance-risk-agent) → HUMAN APPROVAL → ACTION (action_manager)
  → OUTCOME → LEARNING (learning_manager) → MEMORY
  ⟂ security · governance · observability (trace.py) · cost control · evaluation across every layer
```

## Layer separation (the principles, and where each is enforced)
| Principle | Enforced by |
|---|---|
| Skills are capabilities | 30 skills; agents list them in `allowed_skills` |
| Agents are business workers | 17 domain agents + the orchestrator; manifests are the contract |
| Models are reasoning engines | Tier chosen per step, passed as `model` at delegation time; 4 tier agents kept |
| Tools are execution mechanisms | Agents are read-only; only the main session executes, through connectors |
| Memory is institutional context | `memory_graph.py` (facts, graph, ledger, alerts, sources, rules) |
| The Digital Twin is the business state | `twin_state.py` (CURRENT / FORECAST / WHAT-IF / TARGET) over memory |
| Delta determines what changed | `delta_engine.py`; the planner's memory-reuse short-circuit |
| Analytics determines what the data says | T0 scripts; the LLM never does arithmetic |
| Decision Intelligence determines the choices | `decision-intelligence` skill + `decision_record.py` |
| Action Intelligence determines what should happen | `action-center` + action catalog + `action_manager.py` |
| Outcome Learning determines what happened | Ledger outcomes + `learning_manager.py` |
| Governance determines what the AI may do | `policy_gate.py`, the governance-risk-agent, guardrails |

## Why the orchestrator runs in the main session
Sub-agents cannot ask the user questions or approvals, and agent-to-agent spawning would hide tier decisions from the audit trail. The main session is therefore the single orchestrator, approver interface, and writer.
