---
description: "Growth Intelligence: what would you like to do? Start here."
argument-hint: "[request or account]"
---
Growth Intelligence · **What would you like to do?**

Request: $ARGUMENTS

If the request above is empty or only names an account, show the front door: run the growth-discovery skill's
`scripts/prompt_engine.py home` (add `--account <name>` and `--persona <persona>` when known). Present "What would you like
to do?" with the six prompts, then "Explore capabilities" with its categories, in business language only. Run the prompt the
user picks through the business-orchestrator skill. Otherwise, handle the request with the business-orchestrator skill exactly
as if it had been typed.
