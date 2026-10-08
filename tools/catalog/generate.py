"""Generate the YAML starter-prompt catalog from catalog_data.py (single source of truth)."""
import sys, os, yaml
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]   # repository root (= plugin root)
sys.path.insert(0, os.path.dirname(__file__)); from catalog_data import *
OUT = str(ROOT / "skills/growth-discovery/references/starter-prompts")
for f in os.listdir(OUT): os.remove(os.path.join(OUT, f))
for c in CAPS:
    doc = {"capability": {"id": c["id"], "name": c["name"], "description": c["description"], "domain": c["domain"],
           "slash_command": "/" + c["slash"], "aliases": ["/" + a for a in c.get("aliases", [])], "audience": "administrators" if c.get("admin_only") else "all",
           "routes_to": {"skill": c["skill"], "intent": c["intent"]},           # internal routing; never displayed
           "example_outcomes": c["outcomes"],
           "primary_prompts": [dict({"text": x[0], "category": x[1]}, **({"routes_to_capability": x[2]} if len(x) > 2 else {})) for x in c["primary"]],
           "additional_prompts": [{"text": t, "category": k} for t, k in c["additional"]],
           "follow_up_prompts": c["follow"],
           "persona_prompts": c["personas"]}}
    yaml.safe_dump(doc, open(f"{OUT}/{c['id']}.yaml", "w", encoding="utf-8"), sort_keys=False, allow_unicode=True, width=160)
yaml.safe_dump({"catalog_version": "8.0.0", "capabilities": [c["id"] for c in CAPS], "internal_skills": INTERNAL, "explore_categories": EXPLORE,
                "prompt_categories": CATEGORIES, "hubs": HUBS, "global_home": [{"capability": c, "primary_index": i} for c, i in GLOBAL_HOME],
                "variables": {"account": "current account", "opportunity": "current opportunity", "competitor": "current competitor", "meeting": "next meeting", "industry": "current industry", "time_period": "selected period"},
                "template_syntax": "[[with-context|without-context]] — the first branch renders only when every {variable} in it is known"},
               open(f"{OUT}/_index.yaml", "w", encoding="utf-8"), sort_keys=False, allow_unicode=True, width=160)
yaml.safe_dump({p: {"label": l, "home": [{"capability": c, "primary_index": i} for c, i in home]} for p, (l, home) in PERSONAS.items()},
               open(f"{OUT}/_personas.yaml", "w", encoding="utf-8"), sort_keys=False, allow_unicode=True, width=160)
print(len(os.listdir(OUT)), "files")
