# Development guide

## Set up (Windows, macOS or Linux)
```bash
python -m venv .venv
# Windows:      .venv\Scripts\activate
# macOS/Linux:  source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m playwright install chromium     # only for the dashboard and discovery browser tests
```
**Windows:** the code reads UTF-8 files containing characters such as → and €. Run with Python's UTF-8 mode: `set PYTHONUTF8=1` (cmd) or `$env:PYTHONUTF8=1` (PowerShell). VS Code's terminal and tasks in this repository set it for you.

## Test
| Command | Tests | Notes |
|---|---|---|
| `python tests/run_offline.py` | 38 | V7 scenarios and V6.1 regression |
| `python tests/run_v71.py` | 104 | Marketing, financial, competitive threads, correlation, twin, memory |
| `python tests/run_dashboard.py` | 83 | Needs Chromium |
| `python tests/run_prompts.py` | 263 | Starter prompts and discovery; about 5 minutes |
| `bash tests/run_agent_tests.sh` | all of the above, plus live evals | Needs Claude Code; the live evals use your account |

In VS Code: **Terminal → Run Task → "Test: all suites"**.

## Common changes
| To change | Do this |
|---|---|
| Starter prompts or slash commands | Edit `tools/catalog/catalog_data.py`, run `python tools/catalog/regenerate.py`, then `python tests/run_prompts.py`. Never hand-edit the generated YAML, `commands/*.md`, or the "Starter prompts" sections in SKILL.md files |
| An agent | Edit `registry/manifests/<agent>.yaml`, then run `python scripts/registry.py . build`. `agents/*.md` files are generated |
| The demo dashboard | `python tools/build_demo_dashboard.py`, then open `examples/enterprise-growth-command-center.html` |

## Install as a Claude Code plugin
The repository root is the plugin. Validate it with `claude plugin validate .`, then add it through your Claude Code plugin marketplace or local plugin directory.

## Repository layout
`skills/` (36) · `agents/` (generated) · `registry/` · `commands/` (generated) · `policy/` · `schemas/` · `tests/` · `evals/` · `tools/` · `docs/` (including `releases/`) · `examples/`
