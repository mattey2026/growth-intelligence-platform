#!/usr/bin/env python3
"""
trace.py: Execution trace, observability, and cost management.

Every request produces one trace (JSONL, one span per event). Span kinds: request, intent, context, plan,
step, model_call, tool, evidence, decision, action, approval, error, escalation, outcome, answer.
Cost: tokens × an admin-configured price table (policy/price-table.yaml). If no prices are configured,
cost is reported in relative units (T0 0, T1 1, T2 4, T3 12, T4 20 per 1k tokens) and labelled as such.
Latency: measured wall time per span (scripts measured exactly; model latency as reported by the runtime).
USAGE
  trace.py TRACE.jsonl start --request "…" --user u1 --tenant t1                  → prints trace_id
  trace.py TRACE.jsonl span TRACE_ID --kind step --name hypotheses --agent opportunity-agent --tier T3
        --skills growth-opportunity-discovery --data install_base --tokens-in 1450 --tokens-out 900 --latency-ms 8200
        --confidence 0.62 [--escalation "T2→T3: value at stake"] [--error "…"] [--json '{…}']
  trace.py TRACE.jsonl summary [TRACE_ID]      cost per query/agent/recommendation/action, tier mix, escalations
  trace.py TRACE.jsonl html OUT.html           admin observability view
  trace.py TRACE.jsonl check TRACE_ID          V7.1 completeness: request→intent→context→memory→delta→plan→agent→skill→tool→evidence
                                               →decision→approval→action→outcome (core stages required; others where applicable; order enforced)
V7.1 span kinds: marketing_signal_analysis, financial_analysis, competitive_thread_match, competitive_thread_create,
  competitive_thread_update, cross_domain_correlation, evidence_conflict, confidence_change, agent_escalation
"""
import sys, json, uuid, os, yaml, html as H
from datetime import datetime
path, cmd, *rest = sys.argv[1:]
def arg(k, d=None): return rest[rest.index(k) + 1] if k in rest else d
REL = {"T0": 0, "T1": 1, "T2": 4, "T3": 12, "T4": 20}
PT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "policy", "price-table.yaml")
prices = yaml.safe_load(open(PT)) if os.path.exists(PT) else None
def cost(tier, tin, tout):
    if prices and tier in prices.get("tiers", {}):
        p = prices["tiers"][tier]; return round(tin / 1e6 * p["input_per_mtok"] + tout / 1e6 * p["output_per_mtok"], 5), prices.get("currency", "USD")
    return round((tin + tout) / 1000 * REL.get(tier, 0), 3), "relative_units"
def spans():
    return [json.loads(l) for l in open(path)] if os.path.exists(path) else []
if cmd == "start":
    tid = "TR-" + uuid.uuid4().hex[:10]
    open(path, "a").write(json.dumps({"trace_id": tid, "kind": "request", "at": datetime.now().isoformat(timespec="seconds"), "request": arg("--request"), "user": arg("--user"), "tenant": arg("--tenant")}) + "\n")
    print(tid)
elif cmd == "span":
    tid = rest[0]; tier = arg("--tier", "T0"); tin = int(arg("--tokens-in", 0)); tout = int(arg("--tokens-out", 0)); c, unit = cost(tier, tin, tout)
    s = {"trace_id": tid, "kind": arg("--kind", "step"), "at": datetime.now().isoformat(timespec="seconds"), "name": arg("--name"), "agent": arg("--agent"),
         "tier": tier, "skills": (arg("--skills") or "").split(",") if arg("--skills") else [], "data": (arg("--data") or "").split(",") if arg("--data") else [],
         "tools": (arg("--tools") or "").split(",") if arg("--tools") else [], "tokens_in": tin, "tokens_out": tout, "tokens_estimated": "--measured" not in rest,
         "cost": c, "cost_unit": unit, "latency_ms": int(arg("--latency-ms", 0)), "confidence": float(arg("--confidence")) if arg("--confidence") else None,
         "escalation": arg("--escalation"), "error": arg("--error"), **(json.loads(arg("--json")) if arg("--json") else {})}
    open(path, "a").write(json.dumps(s) + "\n"); print(json.dumps({"span": s["name"], "cost": c, "unit": unit}))
elif cmd == "summary":
    S = [s for s in spans() if not rest or s["trace_id"] == rest[0]]
    tr = {}
    for s in S: tr.setdefault(s["trace_id"], []).append(s)
    out = []
    for tid, ss in tr.items():
        calls = [s for s in ss if s["kind"] in ("step", "model_call")]
        by_agent = {}
        for s in calls: by_agent[s.get("agent")] = round(by_agent.get(s.get("agent"), 0) + s["cost"], 3)
        recs = sum(1 for s in ss if s["kind"] == "decision" or (s.get("recommendations") or 0))
        acts = [s for s in ss if s["kind"] == "action" and s.get("state") == "executed"]
        total = round(sum(s["cost"] for s in calls), 3)
        out.append({"trace_id": tid, "request": ss[0].get("request"), "spans": len(ss), "agents": sorted({s.get("agent") for s in calls if s.get("agent")}),
                    "tier_mix": {t: sum(1 for s in calls if s["tier"] == t) for t in REL if any(s["tier"] == t for s in calls)},
                    "escalations": [s["escalation"] for s in ss if s.get("escalation")], "errors": [s["error"] for s in ss if s.get("error")],
                    "tokens": sum(s["tokens_in"] + s["tokens_out"] for s in calls), "tokens_estimated": any(s.get("tokens_estimated") for s in calls),
                    "cost_total": total, "cost_unit": calls[0]["cost_unit"] if calls else None, "cost_by_agent": by_agent,
                    "cost_per_recommendation": round(total / recs, 3) if recs else None, "cost_per_successful_action": round(total / len(acts), 3) if acts else None,
                    "latency_ms_total": sum(s.get("latency_ms", 0) for s in ss),
                    "min_confidence": min([s["confidence"] for s in ss if s.get("confidence") is not None], default=None)})
    print(json.dumps(out, indent=1))
elif cmd == "check":
    # agent / skill / tool form ONE execution phase: skills run inside agents and tools inside skills, and an escalation
    # can follow a skill result, so their relative order is not constrained. Phase order is enforced.
    ORDER = ["request", "intent", "context", "memory", "delta", "plan", "execution", "evidence", "decision", "approval", "action", "outcome"]
    EXEC = {"agent", "skill", "tool"}
    CORE = ["request", "intent", "context", "memory", "delta", "plan", "evidence"]
    STAGE = {"marketing_signal_analysis": "skill", "financial_analysis": "skill", "competitive_thread_match": "skill", "competitive_thread_create": "skill",
             "competitive_thread_update": "skill", "cross_domain_correlation": "skill", "evidence_conflict": "evidence", "confidence_change": "evidence",
             "agent_escalation": "agent", "step": "agent", "model_call": "agent", "escalation": "agent"}
    ss = [s for s in spans() if s["trace_id"] == rest[0]]
    raw = [STAGE.get(s["kind"], s["kind"]) for s in ss]
    seq = ["execution" if x in EXEC else x for x in raw]
    present = [st for st in ORDER if st in seq]
    missing = [st for st in CORE if st not in seq]
    firsts = [seq.index(st) for st in present]
    in_order = firsts == sorted(firsts)
    print(json.dumps({"trace_id": rest[0], "stages_present": present, "execution_detail": sorted({x for x in raw if x in EXEC}), "core_missing": missing, "order_ok": in_order,
                      "v71_events": sorted({s["kind"] for s in ss if s["kind"] in STAGE and s["kind"] not in ("step", "model_call", "escalation")}),
                      "complete": not missing and in_order}, indent=1)); sys.exit(0 if not missing and in_order else 1)
elif cmd == "html":
    S = spans(); tr = {}
    for s in S: tr.setdefault(s["trace_id"], []).append(s)
    rows = ""
    for tid, ss in tr.items():
        req = ss[0].get("request", "")
        steps = "".join(f"<tr><td>{H.escape(str(s.get('kind')))}</td><td>{H.escape(str(s.get('name') or ''))}</td><td>{H.escape(str(s.get('agent') or ''))}</td><td>{s.get('tier','')}</td>"
                        f"<td>{s.get('tokens_in',0)+s.get('tokens_out',0)}</td><td>{s.get('cost','')}</td><td>{s.get('latency_ms','')}</td><td>{'' if s.get('confidence') is None else s['confidence']}</td>"
                        f"<td>{H.escape(str(s.get('escalation') or s.get('error') or ''))}</td></tr>" for s in ss[1:])
        rows += f"<section><h2>{H.escape(req)}</h2><p class=m>{tid} · {ss[0].get('at','')} · user {H.escape(str(ss[0].get('user')))} · tenant {H.escape(str(ss[0].get('tenant')))}</p><div class=t><table><thead><tr><th>Kind</th><th>Step</th><th>Agent</th><th>Tier</th><th>Tokens</th><th>Cost</th><th>ms</th><th>Conf.</th><th>Escalation / error</th></tr></thead><tbody>{steps}</tbody></table></div></section>"
    unit = "USD (configured prices)" if prices else "relative units (no price table configured)"
    page = f"""<!doctype html><html lang=en><head><meta charset=utf-8><meta name=viewport content="width=device-width, initial-scale=1, viewport-fit=cover"><title>Agent observability</title>
<style>:root{{--bg:#F3F5F7;--fg:#1D2733;--mu:#5D6B79;--ln:#D6DDE4;--pp:#FFF;box-sizing:border-box;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}}
@media (prefers-color-scheme:dark){{:root:not([data-theme=light]){{--bg:#10171E;--fg:#E4EAF0;--mu:#98A6B3;--ln:#2A3743;--pp:#17212B}}}}:root[data-theme=dark]{{--bg:#10171E;--fg:#E4EAF0;--mu:#98A6B3;--ln:#2A3743;--pp:#17212B}}
body{{margin:0;background:var(--bg);color:var(--fg);font:14px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}}main{{max-width:1100px;margin:auto;padding:24px 16px}}h1{{font-size:24px;margin:0 0 4px}}h2{{font-size:16px;margin:28px 0 2px}}.m{{color:var(--mu);font-size:12.5px;margin:0 0 8px}}
.t{{overflow-x:auto;border:1px solid var(--ln);background:var(--pp)}}table{{border-collapse:collapse;width:100%;font-size:13px}}th,td{{padding:7px 10px;border-bottom:1px solid var(--ln);text-align:left;white-space:nowrap}}th{{color:var(--mu);font-weight:600}}</style></head>
<body><main><h1>Agent observability</h1><p class=m>{len(tr)} traces · cost in {unit} · token counts are estimates unless marked measured</p>{rows}</main></body></html>"""
    open(rest[0], "w").write(page); print(json.dumps({"written": rest[0], "traces": len(tr)}))
