#!/usr/bin/env python3
"""Strict YAML check for every agent, skill, and eval grader. It complements `claude plugin validate`,
whose parser is more lenient: it accepts `description: A: B` plain scalars that strict YAML parsers reject."""
import glob, sys, yaml, os
root = sys.argv[1] if len(sys.argv) > 1 else "."
bad = 0
AG = {"name", "description", "model", "tools", "disallowedTools", "omitClaudeMd", "maxTurns", "skills", "effort", "background", "memory", "isolation", "color"}
for f in sorted(glob.glob(f"{root}/agents/*.md") + glob.glob(f"{root}/skills/*/SKILL.md") + glob.glob(f"{root}/evals/*/graders/*.md") + glob.glob(f"{root}/evals/*/prompt.md")):
    try:
        fm = yaml.safe_load(open(f).read().split("---")[1])
        if "/agents/" in f:
            assert fm.get("model") in ("haiku", "sonnet", "opus", "fable", "inherit") or str(fm.get("model", "")).startswith("claude-"), "model"
            unknown = set(fm) - AG
            assert not unknown, f"unknown fields {unknown} (Claude Code ignores unknown fields silently)"
            for ign in ("hooks", "mcpServers", "permissionMode"):
                assert ign not in fm, f"{ign} is ignored for plugin agents"
    except Exception as e:
        bad += 1; print(f"FAIL {os.path.relpath(f, root)}: {e}")
print("strict YAML:", "OK" if not bad else f"{bad} failure(s)"); sys.exit(1 if bad else 0)
