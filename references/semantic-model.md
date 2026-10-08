# Canonical Semantic Model (v4.0)

Skills reason over **business concepts**, not vendor schemas. Map every source to these canonical entities before analysis, using `scripts/normalize.py` for tabular data (10 entities: opportunity, account, contact, case, invoice, subscription, product, project, vendor, employee) or explicit mapping for connectors, APIs, and PDFs. Resolve identities with `scripts/entity_resolver.py`. **Never silently invent a mapping**: inferred mappings carry a confidence score, and uncertain mappings that affect the answer are confirmed with the user. Record the mapping and its confidence in the output.

## Canonical entities and common source names

| Canonical entity | Salesforce | Dynamics 365 | HubSpot | SAP / Oracle | ServiceNow / Workday | Spreadsheet headers (typical) |
|---|---|---|---|---|---|---|
| **account** | Account | Account | Company | Customer / Business Partner, Party | Company / Account; Organization | Customer, Client, Account, Company |
| **contact** | Contact | Contact | Contact | Contact Person | Contact; Worker (internal) | Name, Contact, Email |
| **opportunity** | Opportunity | Opportunity | Deal | Sales Opportunity, Quotation (pre-order) | — | Deal, Opp, Pipeline item |
| **product** | Product2 | Product | Product / Line item | Material, Item | Service offering | SKU, Product, Item |
| **contract** | Contract, Subscription | Contract, Agreement | — | Contract, Sales agreement | Contract | Contract, Agreement, Subscription |
| **order / transaction** | Order | Order | — | Sales order, Invoice, AR item | — | Invoice, Order, Booking |
| **case** | Case | Case | Ticket | Service notification | Incident, Case, Request | Ticket, Case, Issue |
| **activity** | Task, Event, EmailMessage | Activity | Engagement | — | — | Email, Meeting, Call log |
| **employee / rep** | User | User | Owner | Employee | Worker (Workday) | Owner, Rep, AE |
| **forecast** | ForecastingItem | Forecast | Forecast | Plan | — | Forecast, Commit |
| **subscription / renewal** | Subscription, Asset, Contract | Contract line | — | Subscription, Contract item | — | Subscription, Renewal, ARR |
| **invoice / revenue** | Invoice (billing) | Invoice | — | Billing document, AR item, GL revenue | — | Invoice, Revenue, Billing |
| **project** | Project (PSA) | Project | — | WBS / Project | Project (SPM) | Project, Engagement |
| **vendor** | — | Vendor | — | Vendor / Supplier | Vendor | Vendor, Supplier |

## Canonical fields (opportunity)

| Canonical field | Meaning | Common synonyms |
|---|---|---|
| `opportunity_id` | Unique deal identifier | Id, Deal ID, Opp ID, Opportunity Number |
| `account_id` | Owning customer | AccountId, Company ID, Customer No |
| `amount` | Deal value in reporting currency | Amount, Deal Value, ACV, TCV, Est. Revenue |
| `currency` | ISO currency code | CurrencyIsoCode, Currency |
| `stage` / `stage_index` | Sales stage and its ordinal position | StageName, Deal Stage, Sales Stage, Pipeline Stage |
| `close_date` | Expected close date | CloseDate, Est. Close, Expected Close |
| `forecast_category` | Seller commitment level | ForecastCategoryName, Forecast, Commit |
| `owner_id` | Seller | OwnerId, Deal Owner, Rep |
| `created_date` | Created date | CreatedDate, Create Date |
| `outcome` | won / lost / open | IsWon + IsClosed, Status, Result |

Other entities follow the same pattern. Extend the table for company-specific objects, and keep the extended version in the data platform or the project.

## Normalization rules
1. **Identity resolution**: match accounts across systems using a shared key first (for example, ERP customer number stored in the CRM), then domain plus name. Report the match rate, and never merge on fuzzy name alone when the value at stake is material.
2. **Stages**: map each source's stages to a canonical ladder (1 Qualify, 2 Discover, 3 Solution, 4 Proposal, 5 Negotiate, 6 Closed). Ask the user to confirm the mapping the first time it is used.
3. **Currency**: convert to the reporting currency with a stated rate and rate date.
4. **Time**: store in UTC, and report in the user's fiscal calendar (confirm the fiscal year start).
5. **System of record by entity**: the CRM for opportunities, ERP or billing for invoices and payments, the service system for cases, HR for employees. When sources conflict, the system of record wins, and the conflict is reported.
6. **Lineage**: every canonical record keeps `source_system`, `source_object`, `source_id`, and `extracted_at`.
