# 7. Cross-Skill Orchestration Model

The user states a **business objective**. Claude plans which skills to compose. The full routing rules are in `references/orchestration.md`.

## Intent → skill chains
| Objective | Chain |
|---|---|
| "Build the account plan for Acme" | data-intelligence → account-360 → buying-committee → account-intelligence-swot-planning (SWOT, whitespace, risk, plan) → deal-intelligence (for major opportunities) → executive brief |
| "Will we hit the quarter?" | data-intelligence → deal-risk → pipeline-forecast-intelligence (P10/P50/P90, what-if) → scenario-planner (if assumptions change) |
| "Help me win Globex" | deal-intelligence (deal-risk + buying-committee + deal-strategy + deal-desk) → close plan → actions |
| "What should I do today?" | daily-growth-briefing (pulls signals from all monitors) |
| "Analyze this spreadsheet" | data-intelligence → the domain skill that matches the detected entity |
| Service issue on a key account | account-360 → renewal radar → account strategist (strategy update) → approved actions |

## Cross-functional signal chain (a core differentiator)
Marketing engagement ↑ → opportunity created → service issues ↑ → adoption ↓ → renewal risk ↑ → finance: account economics ↓ → **account risk detected** → intervention strategy → **human approves** → skills execute authorized actions → **outcome measured**.

In v4, each link is implemented by an existing skill, and `daily-growth-briefing` plus `account-intelligence-swot-planning` connect them. A dedicated `growth-signal-orchestrator` is planned for P2.

## Rules
Pass contracts, not free text, between skills. Carry confidence forward: the combined result is no more confident than its weakest material input. Stop the chain at any approval point.
