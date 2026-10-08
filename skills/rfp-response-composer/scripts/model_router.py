#!/usr/bin/env python3
"""
model_router.py: model routing and escalation policy.

Chooses the lowest-cost capable execution path for a task:
  T0 deterministic  code only (aggregation, statistics, forecasts, finance, thresholds, diffs)
  T1 light          classification, extraction, formatting, basic summary, memory compression
  T2 standard       analysis over retrieved context, account and deal reviews, drafting
  T3 advanced       strategic, cross-functional, scenario, high-value or ambiguous decisions
  T4 expert         highest-stakes, conflicting evidence that T3 could not resolve
and records why. Escalation (Cheap → Moderate → Advanced → Expert) happens only when a
trigger fires: low confidence, conflicting systems, strategic scope, scenario work, high
value at stake, or unresolved ambiguity after a lower tier.

Surface bindings are defined in the policy file (references/model-routing-policy.json):
  claude-code / cowork: plugin subagents with a `model:` field (haiku / sonnet / opus / fable)
  api:                  explicit model IDs
  claude-ai chat:       the conversation's selected model runs all LLM steps; the router
                        still sends T0 work to scripts and logs the recommended tier

USAGE
  python model_router.py route --task "classify dataset" [--rows 50000] [--value-at-stake 9000000]
      [--confidence 0.55] [--conflicts 1] [--strategic 1] [--scenario 1] [--latency low]
      [--surface claude-code] [--policy policy.json]
Prints the tier, the binding for the surface, the reasons, and any escalation.
"""
import argparse, json, re

DEFAULT_POLICY = {
 "tiers": {"T0": "deterministic", "T1": "light", "T2": "standard", "T3": "advanced", "T4": "expert"},
 "bindings": {
   "claude-code": {"T1": "subagent:growth-light (model: haiku)", "T2": "subagent:growth-analyst (model: sonnet)", "T3": "subagent:growth-strategist (model: opus)", "T4": "subagent:growth-expert (model: fable)"},
   "cowork": {"T1": "subagent:growth-light (model: haiku)", "T2": "subagent:growth-analyst (model: sonnet)", "T3": "subagent:growth-strategist (model: opus)", "T4": "subagent:growth-expert (model: fable)"},
   "api": {"T1": "claude-haiku-4-5-20251001", "T2": "claude-sonnet-5", "T3": "claude-opus-5-5", "T4": "claude-fable-5-1"},
   "claude-ai": {"T1": "current model (routing not available in chat)", "T2": "current model", "T3": "current model", "T4": "current model; recommend Opus or higher for this task"}},
 "relative_cost": {"T0": 0, "T1": 1, "T2": 4, "T3": 12, "T4": 20},
 "escalation": {"confidence_below": 0.6, "value_at_stake_above": 1000000, "rows_for_long_context": 200000}}

T0 = r"\b(aggregat\w*|sum|sums|total|count|average|statistic\w*|time.?series|threshold\w*|diff|delta|compute|calculate|arithmetic|backtest|monte carlo|weighted pipeline|kpi calc\w*|variance calc\w*|recogni[sz]e dataset|schema compar\w*)\b"
T1 = r"\b(classif\w*|extract\w*|format\w*|tag\w*|label\w*|basic summar\w*|memory compress\w*|dedup\w*|normali\w*|detect language|simple anomaly)\b"
T3 = r"strateg|decision|scenario|trade.?off|cross.?functional|account plan|swot|executive|negotiat|pricing strategy|win plan|board|investor|what should we"

ap = argparse.ArgumentParser()
ap.add_argument("mode", choices=["route", "policy"])
ap.add_argument("--task", default="")
ap.add_argument("--rows", type=int, default=0)
ap.add_argument("--value-at-stake", type=float, default=0)
ap.add_argument("--confidence", type=float)
ap.add_argument("--conflicts", type=int, default=0)
ap.add_argument("--strategic", type=int, default=0)
ap.add_argument("--scenario", type=int, default=0)
ap.add_argument("--latency", default="normal")
ap.add_argument("--unresolved-after", default="")
ap.add_argument("--surface", default="claude-ai")
ap.add_argument("--policy")
a = ap.parse_args()
P = json.load(open(a.policy)) if a.policy else DEFAULT_POLICY
if a.mode == "policy":
    print(json.dumps(P, indent=1)); raise SystemExit
t = a.task.lower()
reasons, esc = [], []
if re.search(T0, t) and not re.search(T3, t) and not (a.conflicts or a.strategic or a.scenario):
    tier = "T0"; reasons.append("computable deterministically — run in code, no LLM needed")
elif re.search(T1, t) and not re.search(T3, t):
    tier = "T1"; reasons.append("routine extraction / classification / formatting")
elif re.search(T3, t) or a.strategic or a.scenario:
    tier = "T3"; reasons.append("strategic, scenario, or decision-support reasoning")
else:
    tier = "T2"; reasons.append("standard analysis over retrieved context")
order = ["T0", "T1", "T2", "T3", "T4"]
def up(to, why):
    global tier
    if order.index(to) > order.index(tier):
        esc.append(f"{tier} → {to}: {why}"); tier = to
E = P["escalation"]
if tier != "T0":
    if a.confidence is not None and a.confidence < E["confidence_below"]:
        up(order[min(order.index(tier) + 1, 4)], f"confidence {a.confidence} < {E['confidence_below']}")
    if a.conflicts:
        up("T3", "conflicting evidence across systems")
    decisional = re.search(r"\b(recommend\w*|assess\w*|decid\w*|decision|evaluat\w*|interpret\w*|plan\w*|strateg\w*|pric\w*|negotiat\w*)\b", t)
    if a.value_at_stake > E["value_at_stake_above"] and tier in ("T1", "T2") and decisional:
        up("T3" if a.value_at_stake > 5 * E["value_at_stake_above"] else "T2", f"value at stake ${a.value_at_stake:,.0f}")
    if a.unresolved_after:
        up(order[min(order.index(a.unresolved_after) + 1, 4)], f"unresolved after {a.unresolved_after}")
    if a.rows > E["rows_for_long_context"]:
        reasons.append("large data: send aggregates and deltas, not raw rows (layered retrieval)")
if a.latency == "low" and tier in ("T3", "T4") and not a.conflicts:
    reasons.append("low-latency request: answer from the memory summary first, run deep analysis asynchronously")
b = "scripts (no model)" if tier == "T0" else P["bindings"].get(a.surface, {}).get(tier, "current model")
print(json.dumps({"task": a.task, "tier": tier, "tier_name": P["tiers"][tier], "surface": a.surface, "binding": b,
                  "relative_cost": P["relative_cost"][tier], "reasons": reasons, "escalations": esc, "escalated": bool(esc)}, indent=1))
