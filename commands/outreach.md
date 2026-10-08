---
description: "Prospect Research & Outreach: Research a target account and draft first-touch outreach."
argument-hint: "[request or account]"
---
Growth Intelligence request · capability: **Prospect Research & Outreach**

Request: $ARGUMENTS

How to handle this (do not answer from this file; it only routes):
1. If the request above is empty, or is only an account, company or opportunity name, show this capability's starter prompts:
   run the growth-discovery skill's `scripts/prompt_engine.py menu --capability outreach` (add `--account <name>` when one is known
   and `--persona <persona>` when the user's role is known). Show the six prompts in business language, as a numbered list or,
   where the surface supports it, as tappable options; offer "More prompts". Never show internal names. Run the one the user picks.
2. Otherwise, handle the request with the **business-orchestrator** skill exactly as if it had been typed, passing this
   capability to the planner: `agent_planner.py "<request>" --capability outreach`. The same agents, evidence rules, governance,
   approvals and memory apply. Nothing in this command changes what the platform may do.
