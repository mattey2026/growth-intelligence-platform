# Connectors (v5.0): application- and data-source-agnostic

Skills work with **any** authorized source in each category. None is required: files or pasted data can substitute for any connector.

| Category | Examples | Canonical entities supplied |
|---|---|---|
| CRM | Salesforce, Microsoft Dynamics 365, HubSpot, SAP Sales Cloud, Oracle CX, Zoho, custom | account, contact, opportunity, activity, forecast |
| ERP / billing / CPQ | SAP, Oracle, NetSuite, Dynamics F&O, Zuora | order/transaction, contract, product, AR |
| Service / ITSM | ServiceNow, Jira Service Management, Zendesk, Freshservice, Dynamics Customer Service | case |
| HR | Workday, SuccessFactors | employee/rep, capacity |
| Data platform | Snowflake, Databricks, BigQuery, Redshift, SQL Server, Postgres, data lakes | snapshots, history, usage, prediction ledger |
| Files | Excel, CSV, Google Sheets, PDFs (tables) | any entity (profiled and normalized) |
| APIs | REST, GraphQL, custom enterprise apps (via MCP servers) | any entity, mapped via semantic-model.md |
| Marketing | Marketo, HubSpot Marketing, Pardot, Eloqua | campaign, engagement, lead → marketing signals |
| Product analytics | Pendo, Amplitude, Mixpanel, Gainsight PX, warehouse usage tables | usage, adoption → product signals |
| Customer success | Gainsight, Totango, ChurnZero | health, adoption, CTA |
| Partner / PRM | Partner portals, PRM systems | partner pipeline and revenue (P2) |
| CLM | Icertis, DocuSign CLM, Ironclad | contracts, terms, renewals |
| Collaboration | Slack, Teams | activity signals (read); notifications only after approval |
| Email / calendar | Microsoft 365, Google Workspace | activity, contact |
| Meetings | Teams, Zoom, Meet, Webex, conversation-intelligence tools | activity (transcripts) |
| Documents / knowledge | SharePoint, Google Drive, Confluence, Notion | documents, answer libraries |
| BI | Power BI, Tableau, Looker | existing metrics (read) |
| Workflow | Power Automate, ServiceNow Flow, Zapier | actions (approval-gated only) |
| Web | Built in | external signals |

**Bundled as optional examples:** Gmail, Google Calendar, Google Drive (`.mcp.json`). Add your organization's connectors at org level, or in `.mcp.json`.

**Minimum data needed for predictions:** 6–8 quarters of opportunity snapshots or field history (stage, amount, close date, forecast category) from any CRM, or exported to a file.


## V7.1 sources
| Domain | Typical systems | Policy data source | Used by | Minimum fields |
|---|---|---|---|---|
| Marketing | Marketing automation (Marketo, Eloqua, HubSpot, Pardot/MCAE), web analytics, webinar and event platforms, third-party intent providers | `marketing_data` | marketing-intelligence-agent | account/segment/partner, occurred_at, type, source; contact role and campaign optional |
| Financial (public) | Annual reports, results releases, regulatory filings (SEC EDGAR, company IR sites), cited via research | `public_filings`, `web` | financial-intelligence-agent | entity, period, metric, value, source, source_date, basis |
| Financial (internal) | ERP / finance data platform, FP&A, billing (for AR and DSO) | `financial_data` (plus the `financial_confidential` clearance) | financial-intelligence-agent | as above |
| Competitive | CRM competitor fields, RFP distribution lists, call notes and transcripts, win/loss records | `crm`, `transcripts`, `rfps`, `web` | competitive-thread-agent | account_id, competitor_id, observed_at, kind, source |

No connector is bundled. Data arrives through files, the user's connected MCP tools, or the Research agent. Missing sources are reported as data gaps, never filled.

## V7.2 dashboard sources (production_provider.py)
| Source | Populates | If absent |
|---|---|---|
| Business Memory (V7.1 objects and competitive threads) | Threads, risks, competitive exposure, marketing, financial signals, patterns | The section shows what it needs |
| CRM export (workbook or JSON) | Opportunities, contacts, competitors, account revenue | Pipeline-based KPIs are unavailable |
| Monthly billing series (24 months or more) | Revenue (TTM), trends, anomalies | Revenue and trends are "Not available" |
| Quarterly account P&L | Growth, margin, DSO, cost to serve, account economics | Those KPIs are "Not available" |
| Service operations KPIs | Customer and operational health, SLA risks | Those dimensions show "no data" |
| Public filings and events (cited) | Customer financials, financial drivers, market events | The section is empty, with an explanation |
