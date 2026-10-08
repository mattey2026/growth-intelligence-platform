# The Intelligence Loop (v6.0): required for every skill

The platform is a **persistent business intelligence system**, not a stateless chatbot. Every skill runs this loop:

```
1  Identify intent            what is being asked; which answer type (below)
2  Load business context      Business Context Profile from memory (else business-context-discovery)
3  Retrieve relevant memory   L1 summary → L2 open items → L3 facts/changes (business-memory)
4  Check for recent changes   delta_engine / memory delta since the last run for this scope
5  Decide if raw data is needed   only for what changed or what memory cannot answer
6  Select model / tool        model_router.py: deterministic code first; lowest capable tier
7  Analyze                    only the affected portion
8  Compare with history       previous conclusion, previous prediction, and the error
9  Predict / recommend        labelled; respecting stored DECISIONS and PREFERENCES
10 Execute authorized action  approval-gated (guardrails §5–6, §14)
11 Measure outcome            ledger: prediction → actual → error
12 Update the Memory Graph    facts, graph, ledger, summary, run log
```

## Never repeat work unnecessarily
Before any expensive analysis, ask three questions:
1. **Do I already know this?** → Check the memory summary and ledger.
2. **Has anything changed that would invalidate it?** → Check the delta, source freshness, and contradictions.
3. **If nothing changed:** reuse the previous result and report only the delta. **If something changed:** recalculate only the affected part (use `delta_engine.py`'s re-analysis map).

## Answer types
| Type | Question | Primary memory use |
|---|---|---|
| Snapshot | What is happening now? | L3 current state (plus delta, if refreshed) |
| Delta | What changed? | `memory_graph delta --since` |
| Historical | What happened over 12 months? | Fact history, twin, compressed history |
| Predictive | What is likely? | Current state + previous predictions and their errors |
| Prescriptive | What should we do? | + decisions and preferences in force |
| Decision | Options and trade-offs? | + scenarios, previous decisions and their outcomes |
| Continuous | Tell me when it changes | Alert state (business-watch) |
| Memory | What did we decide? | Ledger: decisions |
| Learning | What have we learned? | Ledger: outcomes and applied learnings |

## Output standard for major responses
**CONTEXT** (which business) · **CHANGE** (since when) · **INSIGHT** · **PREDICTION** (labelled) · **RECOMMENDATION** · **ACTION** (approval status) · **MEMORY** (what was saved) · **CONFIDENCE** · **EVIDENCE**

Keep Data → Metric → Insight → Prediction → Recommendation → Action distinct (guardrails §1).

## Memory-aware forecasting
Every forecast is recorded as a prediction with its horizon. When the horizon passes, record the actual and the error. The next forecast shows the previous forecast, what moved it, and the historical error for this kind of forecast.

## Self-learning, honestly
A "learning" exists only as a ledger entry with a proposed rule change. It is applied only after review, and only with sufficient evidence (default: 20 or more comparable outcomes). Never claim the system learned something that is not recorded and applied.
