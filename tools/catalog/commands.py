"""Generate Claude Code slash commands (native plugin mechanism) from the starter-prompt catalog."""
import sys, os, yaml, glob
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]   # repository root (= plugin root)
sys.path.insert(0, os.path.dirname(__file__)); from catalog_data import CAPS, HUBS
OUT = str(ROOT / "commands"); os.makedirs(OUT, exist_ok=True)
for f in glob.glob(OUT + "/*.md"): os.remove(f)
BUILTIN = {"memory": "business-memory"}          # avoid colliding with Claude Code built-in commands
def write(name, desc, hint, body):
    import json as _j   # JSON strings are valid YAML scalars: colons, quotes and '&' are safe
    open(f"{OUT}/{name}.md", "w", encoding="utf-8").write(f"---\ndescription: {_j.dumps(desc, ensure_ascii=False)}\nargument-hint: {_j.dumps(hint)}\n---\n{body}")
ROUTE = """Growth Intelligence request · capability: **{name}**

Request: $ARGUMENTS

How to handle this (do not answer from this file; it only routes):
1. If the request above is empty, or is only an account, company or opportunity name, show this capability's starter prompts:
   run the growth-discovery skill's `scripts/prompt_engine.py menu --capability {cid}` (add `--account <name>` when one is known
   and `--persona <persona>` when the user's role is known). Show the six prompts in business language, as a numbered list or,
   where the surface supports it, as tappable options; offer "More prompts". Never show internal names. Run the one the user picks.
2. Otherwise, handle the request with the **business-orchestrator** skill exactly as if it had been typed, passing this
   capability to the planner: `agent_planner.py "<request>" --capability {cid}`. The same agents, evidence rules, governance,
   approvals and memory apply. Nothing in this command changes what the platform may do.
"""
for c in CAPS:
    if c.get("admin_only"):
        body = ROUTE.format(name=c["name"], cid=c["id"]) + "\nAdministrators only: confirm the user's role allows platform administration before showing or running anything.\n"
    else:
        body = ROUTE.format(name=c["name"], cid=c["id"])
    for nm in [c["slash"]] + c.get("aliases", []):
        write(BUILTIN.get(nm, nm), f"{c['name']}: {c['description']}", "[request or account]", body)
HUB = """Growth Intelligence · **{name}**

Request: $ARGUMENTS

If the request above is empty or only names an account, show the front door: run the growth-discovery skill's
`scripts/prompt_engine.py {cmd}` (add `--account <name>` and `--persona <persona>` when known). Present "What would you like
to do?" with the six prompts, then "Explore capabilities" with its categories, in business language only. Run the prompt the
user picks through the business-orchestrator skill. Otherwise, handle the request with the business-orchestrator skill exactly
as if it had been typed.
"""
write("growth", "Growth Intelligence: what would you like to do? Start here.", "[request or account]", HUB.format(name="What would you like to do?", cmd="home"))
write("sales", "Sales: accounts, opportunities, deals, forecast, meetings and outreach.", "[request or account]", HUB.format(name="Sales", cmd="hub --hub sales"))
print(len(os.listdir(OUT)), "commands:", " ".join("/" + f[:-3] for f in sorted(os.listdir(OUT))))
