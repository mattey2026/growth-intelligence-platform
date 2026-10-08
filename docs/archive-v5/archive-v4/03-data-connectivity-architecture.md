# 3. Data-Source and Connectivity Architecture

```
SOURCES ──► CONNECT ──► SEMANTIC LAYER ──► CANONICAL STORE (optional) ──► SKILLS
```

**Sources**:
- CRM (Salesforce, Dynamics, HubSpot, SAP, Oracle, custom)
- ERP and finance
- ITSM (ServiceNow and others)
- HR (Workday)
- Warehouses and lakes (Snowflake, Databricks, BigQuery)
- SQL, REST, GraphQL
- Excel, CSV, Sheets, PDFs, and other documents
- Email, calendar, transcripts
- Knowledge and collaboration tools
- Web

**Connect**: MCP connectors under the user's own identity; per-system authorization; discovery of available tools.

**Semantic layer**:
- Schema discovery and profiling (`data_profiler.py`).
- Field-meaning inference and canonical mapping, with confidence scores (`normalize.py`, covering 10 entities).
- Identity resolution, duplicates, conflicts, staleness (`entity_resolver.py`).
- Lineage on every record: source system, object, id, extracted-at.

**Canonical store** (optional, enterprise phase): customer's warehouse tables in the canonical schema, holding snapshots, `account_state`, and the prediction ledger.

## Access patterns
| Pattern | When | Example |
|---|---|---|
| **Live query** | Small, current, permissioned reads | Opportunity details, recent emails |
| **Extract and normalize** | Analysis over history | 8 quarters of snapshots for model training |
| **File-first** | No connector yet, or ad hoc | Uploaded pipeline workbook |
| **Warehouse-first** | Enterprise scale | Canonical views in Snowflake or Databricks |

## Rules
- Never silently invent mappings. Inferred mappings carry a confidence score. Low-confidence mappings that affect the result are confirmed with the user.
- The system of record wins per entity (CRM for opportunities, ERP for invoices, ITSM for cases, HR for employees). Conflicts are reported, never hidden.
- Source permissions are inherited, and joins never widen access.
- Staleness is tracked per source and lowers confidence.
