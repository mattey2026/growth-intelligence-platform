# Privacy Policy: Growth Intelligence Platform (Claude plugin)

**Effective date:** 8 October 2026 · **Publisher:** Sumit Mattey (individual developer)

This policy explains what the Growth Intelligence Platform plugin ("the plugin") does with data. The plugin runs inside Claude, Anthropic's AI assistant. Anthropic's handling of your conversations is covered by [Anthropic's Privacy Policy](https://www.anthropic.com/legal/privacy), not by this document.

## 1. What the publisher collects
**Nothing.** The publisher operates no servers, analytics or telemetry for this plugin. No data from your use of the plugin is sent to the publisher.

## 2. Data the plugin stores on your device
| Data | Where | Purpose | How to delete |
|:--|:--|:--|:--|
| **Business Memory:** facts, analyses, decisions, competitive threads, dashboard views you save | SQLite files in your working folder, where Claude runs | So the platform can tell you what changed and learn from outcomes | Delete the memory file (for example `growth_memory.db`) |
| **Traces:** a record of each request's steps, for auditing | Local JSON files in your working folder | Auditability and troubleshooting | Delete the trace files |

Memory files are bound to one tenant; another tenant is refused access. They stay on your device unless you move or share them.

## 3. Connectors (optional, under your control)
The plugin declares three connectors in `.mcp.json`: **Gmail**, **Google Calendar** and **Google Drive**, using Google's official MCP endpoints.
- They work only after **you** sign in to Google and grant access.
- They are used only when a request needs them, for example meeting preparation or a daily briefing.
- Data exchanged with Google is governed by your Google account terms and [Google's Privacy Policy](https://policies.google.com/privacy).
- The plugin does not send connector data anywhere else.
- You can disconnect them at any time in Claude or your Google account.

Other data sources (CRM exports, files, spreadsheets) are used only when you provide them.

## 4. Web research
When a request needs public information (for example a company's published results), Claude may use its web search and fetch tools. Sources are cited in the output.

## 5. Actions and sharing
- **No external action without approval.** Sending an email, updating a CRM record or creating a meeting first passes a policy check, then needs your explicit approval. Pricing and contract commitments are never automated.
- **Dashboards** are published as Claude Artifacts only when you choose to. They stay private until you share them.

## 6. Demo data
The bundled demo uses synthetic data, labelled "DEMO DATA — NOT REAL CUSTOMER DATA". The only real figures are a public company's published financial results, each cited. No personal data is included.

## 7. Children
The plugin is designed for business use and is not directed at children.

## 8. Changes
Changes to this policy are published in this repository with a new effective date. The version history is visible in the repository's commit log.

## 9. Contact
Questions: open an issue at https://github.com/mattey2026/growth-intelligence-platform/issues
