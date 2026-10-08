# 14. Growth Graph: Architecture (P3 foundation)

The twin captures one account over time. The Growth Graph captures **relationships across all entities**, so Claude can reason over connections rather than isolated records.

## Schema
Nodes and edges, each carrying `source`, `as_of`, `confidence`, and ACL tags:
```
(Customer)-[:HAS_UNIT]->(BusinessUnit)-[:EMPLOYS]->(Stakeholder)
(Stakeholder)-[:RELATES_TO {strength, owner}]->(OurEmployee)
(Customer|BU)-[:OWNS {arr, utilization}]->(Product)
(Opportunity)-[:FOR]->(Product); (Opportunity)-[:WITH]->(Customer|BU); (Opportunity)-[:INVOLVES]->(Stakeholder)
(Contract)-[:COVERS]->(Product); (Contract)-[:WITH]->(Customer)
(Invoice)-[:BILLS]->(Contract); (Case)-[:RAISED_BY]->(Customer|BU); (Case)-[:ABOUT]->(Product)
(Usage)-[:OF]->(Product) ; (Competitor)-[:PRESENT_IN {since, source}]->(Customer|BU)
(Signal)-[:ON]->(any); (Risk)-[:AFFECTS]->(Customer|Opportunity); (GrowthOpportunity)-[:TARGETS]->(BU|Product)
(Partner)-[:INFLUENCES]->(Opportunity|Customer)
```

## Queries it enables
- Which stakeholders connect two business units?
- Where do competitors sit relative to our footprint?
- Which service cases touch products tied to open opportunities?
- Which of our executives have paths to a customer's new executive?
- Which peers have the most similar graph neighbourhood (for opportunity propensity)?
- **Graph features for models**: stakeholder centrality, coverage distance, competitor adjacency.

## Build path
| Phase | Scope |
|---|---|
| P1 | Derive a graph view from twin snapshots and canonical tables (in memory, per scope) |
| P2 | Persist in the customer's warehouse as node and edge tables; incremental updates from the signal bus |
| P3 | Graph database or graph-enabled warehouse; graph features in the prediction service; path reasoning in the orchestrator and relationship intelligence |

## Governance
Edge-level ACLs inherit from the source. A traversal never returns a node the user cannot see; paths through hidden nodes are shown only as "path exists (restricted)", if policy allows even that.
