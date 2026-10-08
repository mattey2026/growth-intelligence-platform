"""Insert a generated 'Starter prompts' section into each user-facing SKILL.md (single source: the catalog)."""
import sys, os, re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]   # repository root (= plugin root)
sys.path.insert(0, os.path.dirname(__file__)); from catalog_data import CAPS
SK = str(ROOT / "skills"); BUILTIN = {"memory": "business-memory"}
OPT = re.compile(r"\[\[(.*?)(?:\|(.*?))?\]\]")
res = lambda t: re.sub(r"\s{2,}", " ", OPT.sub(lambda m: m.group(2) or "", t)).replace(" .", ".").replace(" ?", "?").strip()
by_skill = {}
for c in CAPS: by_skill.setdefault(c["skill"], []).append(c)
START, END = "<!-- starter-prompts:start (generated from growth-discovery catalog; do not edit) -->", "<!-- starter-prompts:end -->"
n = 0
for skill, caps in by_skill.items():
    p = f"{SK}/{skill}/SKILL.md"; t = open(p).read()
    t = re.sub(re.escape(START) + r".*?" + re.escape(END) + r"\n?", "", t, flags=re.S).rstrip() + "\n"
    lines = [START, "## Starter prompts", "Show these to users in business language; a chosen prompt goes to the Business Orchestrator. Full catalog and context-aware variants: growth-discovery."]
    for c in caps:
        cmds = ", ".join("/" + BUILTIN.get(x, x) for x in [c["slash"]] + c.get("aliases", []))
        lines.append(f"\n**{c['name']}** ({cmds})" + (" — administrators only" if c.get("admin_only") else ""))
        lines += [f"- {res(x[0])}" for x in c["primary"]]
    lines.append(END)
    open(p, "w", encoding="utf-8").write(t + "\n" + "\n".join(lines) + "\n"); n += 1
print("sections written:", n)
