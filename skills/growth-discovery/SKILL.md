---
name: growth-discovery
description: Growth Intelligence front door — shows curated, ready-to-run business prompts so users never need to know which capability exists. Use when the user asks "what can you do", "help me get started", "show me prompts", "explore capabilities", "what should I ask", opens the platform with no specific request, types /growth or /sales, or finishes a task and would benefit from relevant next steps. Prompts adapt to the current account, persona and live signals (an accelerating competitor, a revenue anomaly, buying intent).
---

> Shared scripts and references live at the plugin root: `../../scripts/` and `../../references/` from this skill's folder.


# Growth Discovery: the Starter Prompt Framework

Version 8.0 · The front door to the Growth Intelligence Platform. The user should think "What do I want to accomplish?", never "Which skill should I use?"

## Rules
1. **Business language only.** Never show skill names, agent names, model tiers, routing, tool names or registry ids. Show the capability's business name (for example "Account Intelligence") and its prompts. Keys starting with `_` in engine output are internal.
2. **Small sets.**
   - Tier 1: six primary prompts.
   - Tier 2: "More prompts", grouped by Discover · Analyze · Investigate · Decide · Prepare · Act · Monitor.
   - Tier 3: contextual prompts, shown **only** when a real signal exists. At most three, one per capability.
   - Never show 30 prompts at once.
3. **Context is inserted automatically.** If the account (or opportunity, competitor or meeting) is known, the prompts name it. Do not ask the user to type what is already known.
4. **Persona adapts the selection,** never the data access. Personas: Investor, CEO, CFO, COO, Growth Operations Head, CRO, Sales Head, Sales Director, Account Executive, Marketing Leader, Customer Success Leader, Operations Leader, IT Leader.
5. **No second reasoning engine.** A chosen prompt is handled by the **business-orchestrator** skill exactly as if typed. When the capability is known (a clicked card, a menu or a slash command), pass it to the planner with `--capability <id>`, so routing is deterministic.
6. **Administration** prompts appear only for administrators.

## Engine (`../../scripts/prompt_engine.py`, JSON output)
| Command | Returns |
|---|---|
| `home [--persona P] [--account A]` | "What would you like to do?" with 6 prompts, plus Explore capabilities (Growth, Sales, Accounts, Customers, Competition, Marketing, Finance, Market, Meetings, Decisions, Dashboards, Operations) |
| `menu --capability ID [--persona P] [--account A] [--more]` | One capability's 6 prompts; `--more` adds Tier 2 by category |
| `hub --hub sales` | The Sales hub (behind `/sales`) |
| `recommend [--persona P] [--account A] [--contract dashboard-contract.json] [--previous "<prompt>"]` | Next best prompts. With a dashboard contract it adds Tier 3 prompts from real signals |
| `followups --after "<prompt>" [--contract C]` | Follow-ups for the completed task, plus contextual ones |
| `resolve --text "<template>" --account A` | Variable resolution |
| `route --text "<prompt>" [--capability ID]` | The orchestration path (used by tests) |

The catalog is in `references/starter-prompts/` (one YAML file per capability, plus `_index.yaml` and `_personas.yaml`). Template syntax: `[[{account}|this account]]` renders "Sanofi" when the account is known, otherwise "this account".

## How to present
- **Claude.ai chat:** where tappable options are available, offer up to four prompts as options plus "More prompts". Otherwise use a short numbered list.
- **Claude Code:** slash commands in `commands/` (for example `/account`, `/threads`, `/growth`) open the same menus.
- **Dashboard:** the Command Center's suggestion row and its "Explore capabilities" drawer show these prompts. Clicking one sends it to the orchestrator with its capability.

After any completed task, offer 3–5 follow-ups from `followups --after "<the prompt>"`. Prefer contextual ones when the result raised a signal.

## Example
**User:** "What can you do?"
→ `home --persona <role> --account <current>` → show "What would you like to do?" and its six prompts, then "Explore capabilities".
