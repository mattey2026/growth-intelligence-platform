# 12. How the Agents Are Built and How They Operate (v6.1)

## Where they live
The agents are **not inside skills**. They are four files in the plugin's `agents/` folder. Claude Code and Cowork register them as `growth-intelligence-platform:<name>`.

| Agent | Model | Tools | Blocked | Preloaded skills | Turn limit |
|---|---|---|---|---|---|
| growth-light | haiku | Read, Grep, Glob | Agent, Write, Edit | — (and does not load project instruction files) | 6 |
| growth-analyst | sonnet | Read, Grep, Glob, Skill | Agent, Write, Edit | business-memory | 12 |
| growth-strategist | opus | Read, Grep, Glob, Skill | Agent, Write, Edit | business-memory, pricing-intelligence | 16 |
| growth-expert | fable | Read, Grep, Glob, Skill | Agent, Write, Edit | business-memory | 16 |

## How they operate
```
Skill step ──► model_router.py ──T0──► script (never delegated)
                     │ T1–T4
                     ▼
            handoff_packet.py  (profile + memory L1–L3 + decisions in force + corrections + delta + T0 outputs)
                     ▼
     Agent tool → growth-intelligence-platform:<agent>   (fresh context; the model from the agent file)
                     ▼  (background by default; wait for the completion notification)
            reply_check.py  → OK │ OK_WITH_ISSUES (verify numbers) │ ESCALATE (→ next tier) │ CONTRACT_FAIL
                     ▼
     Main session: approvals → actions → memory writes → run log (tier, escalations)
```

**Design choices:**
- **One writer.** Agents can't write, edit, or start other agents, so every action and memory write passes through the main session's approval and audit.
- **Packets, not conversations.** Agents see only a compact packet: about 350, 1,000, and 1,450 tokens for T1, T2, and T3 on the test memory, against about 8,100 for the raw workbook.
- **Invented-number guard.** `reply_check.py` flags any number the agent used that isn't in the packet.

## Where it works (verified in Anthropic's documentation)
| Surface | Status |
|---|---|
| Claude Code | Agents load from the plugin's `agents/` folder; the `model:` field applies |
| Cowork | Plugins can bundle sub-agents; the help centre states sub-agents run in Cowork and Claude Code |
| Claude.ai chat | Sub-agents appear greyed out. Skills do the step inline and log the tier they would have used |
| API | Your orchestrator follows the same protocol with model IDs |

## Test status: done here vs needs your environment
| Check | Status |
|---|---|
| Official `claude plugin validate` (plugin + agents), Claude Code 2.1.284 | ✅ Passed |
| Strict YAML validation (agents, skills, graders) | ✅ Passed; the negative test is caught |
| Handoff packets for T1/T2/T3 from the test memory | ✅ Built; sizes measured |
| `reply_check.py` on 4 simulated replies (ok, invented numbers, escalate, contract break) | ✅ All classified correctly |
| Eval suite (5 cases) YAML, regexes, and grader matching | ✅ Validated offline |
| **Real agent launches, actual models, escalation round trip** | ⏳ **Needs your Claude credentials.** Run `tests/run_agent_tests.sh` |
| **`skills:` preload by scoped plugin name** | ⏳ The docs don't state the name format for plugin skills. Agents fall back to loading the skill with the Skill tool if the preload is missing; the analyst eval case checks that business-memory fires |

## Findings from building v6.1
- Claude Code's validator accepts `description: A: B` (a lenient parser), while strict YAML rejects it. The CI therefore runs both validators.
- An administrator setting `CLAUDE_CODE_SUBAGENT_MODEL_FORCE` overrides every agent's model. The run log still records the intended tier.
- In interactive sessions, agents run in the background by default, so the protocol waits for the completion notification before using a result.
