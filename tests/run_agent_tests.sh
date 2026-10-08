#!/usr/bin/env bash
# V8 test runner. Run from the plugin root. Steps 1–6 are free; step 7 makes real model calls on your account.
set -euo pipefail
echo "1/7 Official validation";      claude plugin validate . && claude plugin validate ./agents
echo "2/7 Strict YAML + registry";   python3 tests/validate_strict.py . && python3 skills/platform-admin/scripts/registry.py . validate
echo "3/7 V7.1 suite (104 tests)";           python3 tests/run_v71.py
echo "4/7 V7 regression (30 + 8)";          python3 tests/run_offline.py
echo "5/7 Dashboard suite (83 tests, headless Chromium)"; python3 tests/run_dashboard.py
echo "6/7 Starter prompts and discovery (263 tests)"; python3 tests/run_prompts.py
echo "7/7 Live agent evals (14 cases)"
claude plugin eval . --scaffold --trust-plugin --ablation none --allow-tools "Bash(python3 *)" \
  --runs 3 --judge-model sonnet --max-cost-usd 40 --json tests/last-eval.json || true
echo "Report: evals/results/<timestamp>/report.html. While a live case runs, /tasks shows each agent's model."
