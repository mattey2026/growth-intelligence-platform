# Growth Intelligence Platform V8: Starter Prompts & Discovery

**Version:** 8.0.0 · **Date:** 30 September 2026 · **Status:** **Release candidate**

## Status in one paragraph
Every deliverable is built, and every criterion testable without model calls passes:
- **263/263 starter-prompt tests**;
- no regression: dashboard 83/83, V7.1 104/104, V7 38/38, so **488/488 in total**;
- the official plugin and agent validators, strict YAML, the registry, and all 36 skills.

**Not verified here** (each needs a live Claude session):
1. Slash commands appearing in Claude Code's interactive `/` menu. The files follow Claude Code's documented command format and are validated by our own tests, because Claude Code's validator does not inspect command files.
2. The live `discovery` eval.
3. Typed routing of the *additional* prompts is **86%**, reported rather than claimed as 100%. Clicked prompts and slash commands route deterministically (100%, tested).

## 1. Starter Prompt Framework
**User intent → starter prompt → Business Orchestrator → agent → skill → data → intelligence → decision → action → outcome.**

The framework lives in the new **growth-discovery** skill. Its rules:
- **Business language only.** No skill, agent, model-tier, tool or registry names; tested against every internal name.
- **Small sets.** Tier 1 is 6 primary prompts. Tier 2 is "More prompts" (10–20), grouped by **Discover · Analyze · Investigate · Decide · Prepare · Act · Monitor**. Tier 3 is contextual prompts, shown **only** when a real signal exists (at most 3, one per capability).
- **Context is inserted automatically,** using `[[{account}|this account]]` templates.
- **Persona changes the selection,** never the data access.
- **No second reasoning engine.** A chosen prompt goes to the orchestrator exactly as if typed.

## 2. Global Prompt Catalog
`references/starter-prompts/_index.yaml`:
- the global front door: "What would you like to do?" with 6 prompts;
- 12 Explore categories: Growth, Sales, Accounts, Customers, Competition, Marketing, Finance, Market, Meetings, Decisions, Dashboards, Operations;
- the Sales hub;
- the variables;
- the declared internal skills: the orchestrator, the dashboard renderer, and business-context discovery, which runs automatically.

## 3. Per-capability catalogs
**34 capabilities** cover all **32 user-facing skills**, with 204 primary prompts, 342 additional prompts, example outcomes, follow-ups and persona variants. Two capabilities beyond the brief were needed for full coverage: **Business Watch** (`/watch`) and **Prospect Research & Outreach** (`/outreach`). Appendix B lists every capability's primary prompts.

**Deviations from the brief's wording**, each for a stated reason:

| Brief | V8 | Why |
|---|---|---|
| Meeting: "Give me an executive briefing." | "Give me a pre-meeting executive briefing." | Identical to the Executive Command Center prompt; one card cannot run two analyses |
| Knowledge: "Show me what we learned previously." | "Find lessons from similar past work." | Collided with Memory's "What did we learn previously?" |
| Dashboard: "Show me the biggest opportunities and risks." | "…on the dashboard." | Collided with Executive |
| Competition: "Find competitive displacement opportunities." | "Find where we can displace competitors." | Same text as in Growth Opportunities |
| Account Plan: "Identify expansion opportunities." | "Identify expansion plays for my account plan." | Same text as in Growth Opportunities |
| Admin: "Show me active Skills / Agent performance" | "…active capabilities / assistant performance" | The brief's own rule: no internal terms |
| `/memory` | `/business-memory` | Claude Code has a built-in `/memory` |
| §32 and §39 Solution Architecture; §12 and §38 Pipeline | Merged into one capability each, with `/architecture` and `/pipeline` kept as aliases | Duplicate sections for the same skill |
| A few prompts | Gained an object, e.g. "Extract decisions and actions **from the meeting**" | Routing clarity |

"Map the key stakeholders and relationships" stays in Account Intelligence but runs **Relationships**, through a prompt-level cross-link.

## 4. Persona Prompt Catalog
`_personas.yaml` covers 13 personas, each with a 6-prompt front door: Investor, CEO, CFO, COO, Growth Operations Head, CRO, Sales Head, Sales Director, Account Executive, Marketing Leader, Customer Success Leader, Operations Leader, IT Leader. Capability menus also carry persona variants, for example the Sales Director's "Show me which deals need intervention" and the Investor's "Show me the company's growth, profitability and strategic risks". Appendix B shows every persona's front door.

## 5. Contextual Prompt Engine
`prompt_engine.py recommend` reads the live signals in a Dashboard Contract:
- accelerating competitive threads;
- displacement opportunities;
- anomalies;
- weakening key relationships;
- intent surges;
- probability drops;
- margin compression;
- pending decisions;
- changes.

Each prompt it produces names the subject and says why it was suggested. **Example (demo):** "Investigate the Competitor X threat" (thread accelerating), "Explain the revenue anomaly in 2026-06" (anomaly detected). Without a signal, no contextual prompt appears (tested).

## 6. Follow-up Prompt Engine
`followups --after "<prompt>"` combines three sources:
- the capability's follow-ups;
- the next workflow step (for example Discover → Analyze → Investigate → Decide → Act → Monitor);
- contextual prompts from the result's signals.

It deduplicates, never repeats the executed prompt, and caps at 5. **Example:** after "Build my complete account strategy" with the Sanofi contract, it suggests the Competitor X threat, the biggest opportunity, the buying committee, and a 90-day plan.

## 7. Slash commands
`commands/` holds 38 Claude Code commands:
- a command for each capability (including every one listed in the brief);
- the aliases `/pipeline` and `/architecture`;
- the hubs `/growth` and `/sales`.

Each command only routes:
- **without a request**, it shows the capability's six prompts, with context;
- **with a request**, it hands the request to the business orchestrator with `--capability`.

Tests check that each file has valid frontmatter, routes to the orchestrator, contains no business logic, and keeps internal names out of the description users see.

## 8. Tests (`tests/run_prompts.py`, 263 tests)
| Area | Result | What it checks |
|---|---|---|
| Coverage | 39/39 | 34 capabilities plus catalog integrity: no orphan files, valid intents and cross-links, every user-facing skill covered |
| Quality | 37/37 | Verb- or question-led, ≤ 14 words, end punctuation, no internal terms, valid templates, no stuck words, unique primaries across capabilities, ≥ 95% of primaries ≤ 12 words |
| Routing, typed (primary) | 34/34 | All 204 primary prompts reach their capability by text alone |
| Routing, clicked or command | 34/34 | All 546 prompts reach their capability and intent with the hint |
| Follow-ups | 36/36 | Generated, resolved, routable, relevant, never the executed prompt |
| Slash commands | 34/34 | Valid, routing-only, business-language descriptions |
| Personas | 19/19 | 13 personas × 6 distinct routable prompts; CEO, Sales Director, AE and Investor expectations from the brief |
| Context | 5/5 | Account and competitor insertion; generic fallback; no unresolved braces anywhere |
| Contextual tier | 5/5 | Signal prompts only with signals; at most 3; small sets |
| Discovery | 9/9 | Front door, 12 Explore categories, not sales-only, admin gated, `/sales` hub, no orphan or built-in-clashing commands, every brief command present |
| Dashboard | 7/7 | Engine-driven suggestions; Explore drawer; click hand-off with capability (in Chromium) |
| Catalog sync | 2/2 | SKILL.md sections match the catalog; no invented frontmatter |
| Registry | 2/2 | Valid; discovery skill reachable |
| **Total** | **263/263** | |

**Regression:** dashboard 83/83 · V7.1 104/104 · V7 38/38. **Total 488/488.**

**Routing, measured:**

| Prompts | Before V8 | After V8 |
|---|---|---|
| Primary, typed | 103/204 (50%) | **204/204** |
| Additional, typed | — | 295/342 (**86%**, reported, not asserted) |
| All, clicked or command | — | 546/546 |

## 9. Updated Skill registry
`registry/skill-registry.json` (v8.0.0) records each skill's audience (users, administrators or internal), its capabilities and commands, the agents that use it, and its scripts. The orchestrator manifest now owns growth-discovery. The registry validator's "every skill reachable" rule caught the missing assignment.

## 10. Documentation
README (start with `/growth`), ARCHITECTURE (front door), CHANGELOG 8.0.0, tests/README, docs/18 (this report), docs index, the growth-discovery SKILL.md, and generated Starter prompts sections in 32 SKILL.md files.

## 11. Files
See Appendix A (generated by diffing V7.2 and V8).

## 12. Defects found and fixed during the build
- **Routing.** Half of the platform's own capabilities were unreachable by typed requests: relationships, win/loss, briefing, signals, knowledge, outreach and admin had no intent, and "health of this deal" went to *customer* health. Typed routing of primaries rose from 103/204 to 204/204, within the existing orchestrator.
- **Invalid YAML in all 38 command files** (unquoted colons). Claude Code's validator does not parse command files, so our tests now do.
- **`/sales` crashed on first use** (an argument-order bug).
- **Five ambiguous prompts** shared text across capabilities.
- **The dashboard could claim "copied"** when the browser refused the clipboard. It now shows the text to copy.
- **A template bug** produced "Watchthis account".
- **Contextual prompts crowded out** the persona's prompts.
- **Thread prompts stayed generic** although the competitor was known.

## 13. Known limitations
1. **Live surfaces are not verified.** Command display in Claude Code's `/` menu and the live `discovery` eval need a live session (`bash tests/run_agent_tests.sh`, step 7).
2. **Claude.ai chat does not load plugin slash commands.** There, discovery comes from the growth-discovery skill ("What can you do?"), which offers tappable options where the surface supports them (up to four at a time), and from the dashboard.
3. **Typed routing of additional prompts is 86%.** The classifier is pattern-based, and some phrasings ("What should I do next?") are inherently ambiguous without context. Clicked prompts carry their capability and route exactly.
4. **Published dashboards cannot post into the chat.** Prompts are copied with their context, or shown for copying when the browser refuses.
5. **The persona is supplied by context or role,** not detected automatically.
6. **Contextual signals** come from a Dashboard Contract or a signals file. Business Watch firings and Business Memory do not yet feed them directly.
7. **Prompt quality is rule-checked,** not user-tested.

## 14. Next-release (V9) recommendations
1. A model-assisted intent classifier as a fallback when no pattern matches, so typed additional prompts reach 100% without growing the pattern list.
2. Feed Business Watch firings and Business Memory changes into Tier 3 directly.
3. Learn prompt ranking from usage (which prompts users run and complete), per persona.
4. Automatic persona detection from identity and role, with user override.
5. Live data binding for published dashboards, so a clicked prompt can post into the conversation.
6. Carried forward: hard enforcement of the policy gate (PreToolUse hook) and PII redaction.

---
## Appendix A: Files created and modified (V7.2 → V8)

### Created (82)

- `commands/*.md` — 38 files
- `skills/growth-discovery/references/starter-prompts/*.yaml` — 37 files
- `evals/discovery/case.yaml`
- `evals/discovery/fixture.sh`
- `evals/discovery/graders/answer-quality.md`
- `evals/discovery/prompt.md`
- `skills/growth-discovery/SKILL.md`
- `skills/growth-discovery/scripts/prompt_engine.py`
- `tests/run_prompts.py`

### Modified (47)

- `.claude-plugin/plugin.json`
- `ARCHITECTURE.md`
- `CHANGELOG.md`
- `README.md`
- `docs/00-index.md`
- `registry/manifests/business-orchestrator.yaml`
- `registry/skill-registry.json`
- `schemas/dashboard.schema.json`
- `skills/*/SKILL.md (generated Starter prompts section)` — 32 files
- `skills/artifact-dashboard-intelligence/assets/command-center.core.js`
- `skills/artifact-dashboard-intelligence/assets/command-center.css`
- `skills/artifact-dashboard-intelligence/assets/command-center.widgets.js`
- `skills/business-orchestrator/scripts/agent_planner.py`
- `skills/dashboard-intelligence/scripts/dashboard_builder.py`
- `tests/README.md`
- `tests/run_agent_tests.sh`

### Removed (0)

- none

## Appendix B: Catalog summary (generated from the catalog)
## Global front door (no persona)
**What would you like to do?**

- ▶ Build my complete account strategy.
- ▶ Find my biggest growth opportunities.
- ▶ Prep me for my next sales call.
- ▶ Review my pipeline for risks and next steps.
- ▶ What has changed in this account?
- ▶ Give me today's growth briefing.

**Explore capabilities:** Growth · Sales · Accounts · Customers · Competition · Marketing · Finance · Market · Meetings · Decisions · Dashboards · Operations

## Persona front doors
- **Investor:** Give me the state of the business. · Show me the financial story. · Show me the major market trends. · Show me where competitors are gaining ground. · Run a best, base and worst-case scenario. · Show me the biggest risks.
- **CEO:** Give me the state of the business. · Show me the strongest growth signals. · Find my biggest growth opportunities. · Show me the biggest risks. · Help me evaluate this decision. · Give me today's growth briefing.
- **CFO:** Show me the financial story. · Run forecast scenarios. · Run a best, base and worst-case scenario. · Analyze the discount on this deal. · Show me accounts at renewal risk. · Prepare an executive decision brief.
- **COO:** Give me the state of the business. · Show me my highest-priority actions. · Identify renewal risks. · Compare strategic scenarios. · Find anomalies in this data. · Watch my strategic accounts for risk.
- **Growth Operations Head:** Show me the strongest growth signals. · Which campaigns are influencing pipeline? · Show me pipeline coverage. · Find whitespace. · Show me my growth command center. · Give me today's growth briefing.
- **CRO:** Build my sales forecast. · Review my pipeline for risks and next steps. · Find my biggest growth opportunities. · Show me where competitors are gaining ground. · Identify recurring loss patterns. · Show me my growth command center.
- **Sales Head:** Review my pipeline for risks and next steps. · Build my complete account strategy. · Find my biggest growth opportunities. · Identify competitive threats. · Give me today's growth briefing. · What has changed in this account?
- **Sales Director:** Identify stalled opportunities. · Tell me what could prevent us from winning. · Show me relationship risks. · Which competitive threads are accelerating? · Show me my highest-priority actions. · Prep me for my next sales call.
- **Account Executive:** Prep me for my next sales call. · Build my complete account strategy. · Find my biggest growth opportunities. · Tell me what I should do next on this deal. · Tell me who I should engage next. · What needs my attention today?
- **Marketing Leader:** Which campaigns are influencing pipeline? · Identify accounts showing buying intent. · Which accounts are warming? · Show me the strongest growth signals. · Show me recent competitive signals. · Find my biggest growth opportunities.
- **Customer Success Leader:** Show me accounts at renewal risk. · Find expansion opportunities with existing customers. · Show me adoption changes. · Show me relationship risks. · Show me the current customer state. · Show me my highest-priority actions.
- **Operations Leader:** Find unusual patterns in the business. · Show me overdue actions. · Find anomalies in this data. · Run a best, base and worst-case scenario. · Watch my strategic accounts for risk. · Show me the biggest risks.
- **IT Leader:** Create the target architecture. · Identify integration requirements. · Analyze this dataset. · Search our previous work. · Identify architecture and technical risks. · Analyze this industry.

## Per-capability primary prompts

| Capability | Command | Primary prompts | More |
|---|---|---|---|
| Account Planning & SWOT | /account-plan | Build my account plan. · Create an evidence-backed SWOT. · Identify expansion plays for my account plan. · Identify account risks. · Show me whitespace. · Recommend my account plays. | 10 |
| Account Intelligence | /account | Build my complete account strategy. · What has changed in this account? · Show me the biggest growth opportunities. · Identify the major risks in this account. · Map the key stakeholders and relationships. · Give me an executive briefing on this account. | 10 |
| Actions | /actions | Show me my highest-priority actions. · What should I do today? · Show me overdue actions. · Prioritize my actions. · Show me actions linked to opportunities. · Show me actions linked to risks. | 10 |
| Platform Administration | /admin | Show me platform health. · Show me active capabilities. · Show me assistant performance. · Show me errors. · Show me usage. · Show me governance events. | 10 |
| Business Analysis | /bi | Analyze my business. · What should I know today? · What changed in the business? · Find unusual patterns in the business. · Show me the most important signals. · Tell me what needs attention. | 10 |
| Daily Briefing | /briefing | Give me today's growth briefing. · What changed overnight? · What needs my attention today? · Show me today's opportunities. · Show me today's risks. · Give me my top priorities for today. | 10 |
| Competitive Intelligence | /competition | Show me the competitive landscape. · Identify competitive threats. · Show me where competitors are gaining ground. · Find where we can displace competitors. · Analyze this competitor. · Show me recent competitive signals. | 10 |
| Customer Growth | /customer-growth | Find expansion opportunities with existing customers. · Identify customer growth signals. · Show me adoption changes. · Identify renewal risks. · Find whitespace in our customer base. · Build a customer growth plan. | 10 |
| Dashboards | /dashboard | Show me my growth command center. · Show me what changed on the dashboard. · Build the dashboard I need for this account. · Show me opportunities and risks on the dashboard. · Create an executive dashboard. · Analyze this dashboard. | 10 |
| Data Analysis | /data | Analyze this dataset. · What patterns do you see in this data? · Find anomalies in this data. · Explain the key drivers in this data. · Build an analytical summary of this data. · Create a decision-ready view of this data. | 10 |
| Deal Strategy | /deal | Assess the health of this deal. · Tell me what could prevent us from winning. · Build my deal strategy. · Identify the missing stakeholders. · Show me the competitive risks in this deal. · Tell me what I should do next on this deal. | 10 |
| Decision Support | /decision | Help me evaluate this decision. · Show me the options and trade-offs. · What evidence supports each option? · What are the risks of each option? · Run a scenario analysis for this decision. · Prepare an executive decision brief. | 10 |
| Customer Digital Twin | /digital-twin | Show me the current customer state. · What's changed in the customer twin? · Show me historical trends. · Show me the customer forecast. · Run a what-if scenario on this customer. · Show me the target state. | 10 |
| Executive Command Center | /executive | Give me the state of the business. · What changed materially? · Show me the biggest opportunities. · Show me the biggest risks. · What should leadership focus on? · Give me an executive briefing. | 10 |
| Financial Intelligence | /financial | Show me the financial story. · Analyze the last five years of financials. · What financial changes matter? · Show me margin and profitability trends. · Find financial signals that could create opportunities. · Explain the financial position. | 10 |
| Meeting Follow-through | /followup | Process my call notes into follow-ups. · Extract decisions and actions from the meeting. · Create follow-up tasks from the meeting. · Identify commitments made in the meeting. · Update the account intelligence from the meeting. · Update the opportunity based on this meeting. | 10 |
| Pipeline & Forecast | /forecast, /pipeline | Review my pipeline for risks and next steps. · Build my sales forecast. · Show me pipeline coverage. · Identify stalled opportunities. · Show me forecast risks. · Run forecast scenarios. | 12 |
| Knowledge | /knowledge | Find the relevant knowledge for this account. · Search our previous work. · Find similar situations we've handled. · Find lessons from similar past work. · Find supporting evidence for this claim. · Summarize the relevant knowledge. | 10 |
| Market Intelligence | /market | What's changing in this market? · Show me the major market trends. · Identify growth opportunities from market changes. · Show me emerging market threats. · Analyze this industry. · Tell me what I should be watching in the market. | 10 |
| Marketing Intelligence | /marketing | Show me marketing activity affecting this account. · Identify accounts showing buying intent. · Show me marketing engagement trends. · Which campaigns are influencing pipeline? · Which accounts are warming? · Show me marketing-to-revenue signals. | 10 |
| Meeting Preparation | /meeting | Prep me for my next sales call. · Give me a pre-meeting executive briefing. · Show me what I need to know before this meeting. · Identify the customer's priorities. · Tell me what questions I should ask. · Prepare my meeting strategy. | 10 |
| Business Memory | /business-memory | What do we already know about this account? · Show me the history. · What did we learn previously? · What decisions have we made? · Show me previous outcomes. · Update the business memory. | 10 |
| Growth Opportunities | /opportunities | Find my biggest growth opportunities. · Find whitespace. · Identify expansion opportunities. · Find competitive displacement opportunities. · Show me why these opportunities matter. · Prioritize my opportunities. | 10 |
| Prospect Research & Outreach | /outreach | Research this prospect for me. · Why this account, why now, why us? · Draft outreach to the CIO. · Find a reason to reach out. · Prioritize my target accounts. · Personalize my outreach sequence. | 10 |
| Pricing | /pricing | Analyze the pricing for this deal. · Should we change the commercial structure? · Show me pricing benchmarks. · Analyze the discount on this deal. · Model pricing scenarios. · Show me the margin impact of this price. | 10 |
| Relationships | /relationships | Map the key stakeholders. · Show me relationship risks. · Identify my strongest relationships. · Show me executive engagement. · Identify missing relationships. · Tell me who I should engage next. | 10 |
| Renewals & Expansion | /renewals | Show me accounts at renewal risk. · Identify expansion-ready accounts. · Find churn signals. · Show me renewal drivers. · Identify customer health changes. · Build my renewal strategy. | 10 |
| RFP Response | /rfp | Analyze this RFP. · Build an RFP response strategy. · Identify the customer's evaluation criteria. · Identify our gaps in this RFP. · Analyze our competitive positioning for this RFP. · Draft the RFP response structure. | 10 |
| Scenario Planning | /scenario | Run a best, base and worst-case scenario. · What happens if this deal slips? · Model the impact of losing this customer. · Model the impact of winning this opportunity. · Compare strategic scenarios. · Show me the financial impact of this scenario. | 10 |
| Growth Signals | /signals | Show me the strongest growth signals. · Find emerging opportunities across my accounts. · Find compound signals across my accounts. · Show me accounts becoming more attractive. · Show me accounts becoming risky. · Explain why this signal matters. | 10 |
| Solution Design | /solution, /architecture | Design a solution for this opportunity. · Create the target architecture. · Map business requirements to capabilities. · Identify integration requirements. · Identify architecture and technical risks. · Create an executive solution overview. | 10 |
| Competitive Threads | /threads | Show me active competitive threads. · Which competitive threads are accelerating? · Explain this competitive thread. · Show me the evidence behind this threat. · Predict what this competitor could do next. · What should I do about this threat? | 10 |
| Business Watch | /watch | Alert me when a big deal slips. · Watch my strategic accounts for risk. · Tell me if a competitor enters my accounts. · Alert me when coverage drops below target. · Notify me if an executive sponsor leaves. · Show me what my watches found. | 10 |
| Win/Loss | /winloss | Analyze why we won. · Analyze why we lost. · Identify recurring loss patterns. · Show competitive win/loss patterns. · Find lessons from historical deals. · Recommend changes based on past outcomes. | 10 |