# Growth Intelligence Platform: V8 Enterprise Growth & Decision Intelligence

**Start here:** type `/growth` (Claude Code), or ask "What can you do?" (any surface). You get "What would you like to do?" with six ready-to-run prompts for your role and current account, and **Explore capabilities** across Growth, Sales, Accounts, Customers, Competition, Marketing, Finance, Market, Meetings, Decisions, Dashboards and Operations.

Ask in business terms; the platform decides which agents, skills, data, tools, and model tier to use. You never name a skill or agent.

**Examples:** "Show me my Sanofi dashboard." · "What's changing in this account?" · "Show me the financial story." · "What is marketing telling us?" · "Where are competitors gaining ground?" · "Find the biggest growth opportunities." · "Build a complete account strategy." · "Find $20M of opportunity in <account>" · "Challenge your recommendation" · "Execute this"

## Getting started (developers)
- **Windows, one step:** run `setup-windows.ps1` (creates the folder, first commit, private GitHub repository, Python environment, and opens VS Code).
- **Manual setup:** see `docs/DEVELOPMENT.md` (environment, tests, regenerating prompts, building the demo dashboard).
- **Demo dashboard:** open `examples/enterprise-growth-command-center.html` in a browser (demo data).
- **Release history:** `docs/releases/` and `CHANGELOG.md`.

## How it works
| Layer | Role |
|---|---|
| **Starter prompts** (growth-discovery) | 34 capabilities × 6 primary prompts (plus 342 more by category), 13 personas, context insertion, signal-driven suggestions, follow-ups; 38 slash commands. Every prompt routes through the orchestrator |
| **Business Orchestrator** (skill, main session) | Plans with `agent_planner.py`, **discovers agents from the registry** by the intents they serve, answers "what changed" first, delegates, validates evidence, governs, acts after approval, remembers |
| **21 domain agents** (generated from `registry/manifests/`) | Least privilege; they analyse and *propose*, they never act. New in V7.2: Dashboard Intelligence. New in V7.1: Marketing Intelligence, Financial Intelligence, Competitive Thread |
| **4 reasoning tiers** | T0 code for every calculation, then T1–T3 models; T4 never by default |
| **36 skills** | Adds growth-discovery (V8), dashboard-intelligence and artifact-dashboard-intelligence (V7.2), and three V7.1 intelligence skills |
| **Dashboard layer** | Provider (demo or production) → T0 builder → **Dashboard Contract** (`schemas/dashboard.schema.json`) → renderer (first: the Enterprise Growth Command Center Claude Artifact). Nine personas, one intelligence layer |
| **Cross-domain correlation** | Patterns P1–P5 (marketing→growth, financial→growth, financial→risk, competitive displacement, compound) as labelled hypotheses |
| **Memory, twin and delta** | Typed memory objects, persistent CompetitiveThreads, twin state domains, cross-domain delta |
| **Governance** | Policy gate (tenant, RBAC/ABAC, agent and data permissions, financial-data clearance) → human approval → auditable action manager |
| **Evidence contract** | FACT / INFERENCE / CORRELATION / HYPOTHESIS / PREDICTION / RECOMMENDATION; fabricated values rejected |
| **Observability** | `trace.py` with V7.1 events and a completeness check |

## Where it runs
| Surface | Behaviour |
|---|---|
| **Claude Code / Cowork** | Full agent delegation with per-step model routing |
| **Claude.ai chat** | Skills and the orchestrator run, with agent steps done inline under each agent's contract |

## Test it
```bash
python3 tests/run_prompts.py          # 263 starter-prompt and discovery tests
python3 tests/run_dashboard.py        # 83 dashboard tests (headless Chromium)
python3 tests/run_v71.py              # 104 V7.1 tests (no model calls)
python3 tests/run_offline.py          # 30 V7 scenarios + 8 V6.1 regression checks
bash tests/run_agent_tests.sh         # validation + all suites + 14 live eval cases (live cases use your account)
```
See `tests/README.md` for what each suite covers.

## Docs
`ARCHITECTURE.md` · `CONNECTORS.md` · `CHANGELOG.md` · `docs/18-v8-starter-prompts.md` · `docs/17-v72-dashboard.md` · `docs/15-v71-intelligence.md` · `registry/agent-registry.json` · `registry/skill-registry.json` · `docs/14-v7-report.md`
