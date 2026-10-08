# Delegation Protocol (v6.1)

This protocol turns model routing from a recommendation into a procedure. The **main session is the orchestrator**: it routes, delegates, checks replies, writes memory, and takes actions. **Tier agents only analyse and propose.**

## When delegation applies
| Surface | Delegation |
|---|---|
| Claude Code, Cowork | ✅ Plugin agents are available (confirmed in Anthropic's docs: sub-agents run in Cowork and Claude Code, and are greyed out in chat) |
| Claude.ai chat | ❌ Agents don't run. Do the step inline on the current model; log `--tier <recommended> --reason "chat: inline"` |
| API | Your orchestrator follows the same steps and passes model IDs directly |

## The procedure (every non-T0 step)
1. **Route.** Run `python scripts/model_router.py route --task "<step>" [--value-at-stake N] [--conflicts 1] [--confidence C] --surface <claude-code|cowork>`.
   - T0 → run the script yourself. **Never delegate arithmetic.**
2. **Build the packet.** Run `python scripts/handoff_packet.py <memory.db> --task "<step>" --tier <T> --entity <id> [--scope <topic>] [--since <last run>] [--attach <T0 outputs>] --out packet.md`.
   - The packet holds the profile, memory recall (L1 for T1; L1–L2 for T2; L1–L3 for T3/T4), decisions in force, corrections, the delta, and pre-computed analytics. Nothing else. The agent does **not** see the conversation.
3. **Delegate.** Call the Agent tool with the agent's **scoped name** and the packet as the prompt:

   | Tier | Agent | Model |
   |---|---|---|
   | T1 | `growth-intelligence-platform:growth-light` | haiku |
   | T2 | `growth-intelligence-platform:growth-analyst` | sonnet |
   | T3 | `growth-intelligence-platform:growth-strategist` | opus |
   | T4 | `growth-intelligence-platform:growth-expert` | fable |

   The agent file's `model:` applies. To escalate *within the same agent* (a rare case), pass the per-invocation `model` parameter, which overrides the file.
4. **Wait for the result.** In interactive sessions, agents usually run in the background, and the result arrives as a completion notification in a later turn. Do not report results before it arrives.
5. **Check the reply.** Save the reply to a file and run `python scripts/reply_check.py reply.txt --packet packet.md --current-tier <T>`.

   | Exit code | Status | What to do |
   |---|---|---|
   | 0 | OK | Use the result |
   | 0 | OK_WITH_ISSUES | Verify any **unverified numbers** with scripts, or drop them. Fix missing labels before presenting |
   | 3 | ESCALATE | Go back to step 2 with `--tier <next_tier>`, attaching the lower tier's partial analysis. At T4, stop and ask the user or a human expert |
   | 1 | CONTRACT_FAIL | Re-delegate once with the contract restated; if it fails again, do the step inline and log it |

6. **Act and remember (main session only).** Apply approvals (guardrails §5–6), then write memory:
   - `memory_proposals` from the agent → `memory_graph.py record …` (after review);
   - `run-log <RUN> --tier <final tier> --reason "<router reason>; escalations: …" --escalated 0/1`.

## Rules
- **One writer.** Agents never write memory, files, or systems, and never start other agents (`disallowedTools: Agent, Write, Edit`). This keeps every tier decision and every write in the main session's run log and approval flow.
- **Evidence from the packet only.** Numbers must come from the packet. `reply_check.py` flags any that don't.
- **Decisions in force.** They travel in every T2+ packet, and recommendations must reference them (guardrails §19).
- **Escalate at most one tier at a time.** T4 requires a written reason from T3.
- **Transparency.** Tell the user when a step was delegated or escalated, in one line (for example "Pricing analysed by the strategist tier after the analyst tier escalated on conflicting evidence"). Detail goes to the run log.
