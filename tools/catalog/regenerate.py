"""Regenerate the starter-prompt catalog, slash commands and SKILL.md 'Starter prompts' sections from catalog_data.py.
Edit catalog_data.py, then run:  python tools/catalog/regenerate.py   and re-run  python tests/run_prompts.py"""
import subprocess, sys, os
here = os.path.dirname(os.path.abspath(__file__))
for s in ("generate.py", "commands.py", "skill_sections.py"):
    subprocess.run([sys.executable, os.path.join(here, s)], check=True)
