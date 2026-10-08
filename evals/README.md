# Delegation eval suite (`claude plugin eval`)

These five cases check that model routing works in practice, not only on paper:

| Case | Checks |
|---|---|
| no-delegate-arithmetic | Arithmetic is **not** delegated (Agent called 0 times) and the answer is right |
| light-extraction | Extraction goes to `growth-light` (haiku); nothing is claimed as saved |
| analyst-status-from-memory | business-memory skill fires; handoff packet built; `growth-analyst` (sonnet) answers from memory facts |
| strategist-pricing-decision | `growth-strategist` (opus) handles pricing and respects the CRO decision |
| escalation-roundtrip | Analyst runs before strategist (escalation); `reply_check.py` used |

Run from the plugin root (Claude Code v2.1.269+; git 2.31+; these are real model calls on your account):

```bash
claude plugin validate .
claude plugin eval . --scaffold --trust-plugin --ablation none \
  --allow-tools "Bash(python3 *)" --runs 3 --max-cost-usd 15 --judge-model sonnet
```

- `--scaffold` copies the two-review test memory into each run.
- `--ablation none` is used because a no-plugin baseline cannot call plugin agents; that failure is expected.
- To confirm which model each agent actually ran on, open the report's transcripts, or run the case interactively and use `/tasks` while the agent is running.

## V7.1 cases
| Case | Checks |
|---|---|
| `marketing-agent` | Delegates to the marketing-intelligence-agent; correlation vs causation; roles; intent |
| `financial-agent` | Reported metrics; EBITDA, capex, DSO and cash reported missing, not estimated |
| `competitive-thread-agent` | Three signals form one thread; momentum, prediction, approval |
| `sanofi-strategy-v71` | Integrated account view using all three new agents; evidence per conclusion; no fabrication |
