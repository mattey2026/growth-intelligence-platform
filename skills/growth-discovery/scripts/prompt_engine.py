#!/usr/bin/env python3
"""
prompt_engine.py: Starter Prompt Framework engine (Growth Discovery, V8).

Serves curated, business-language prompts. It never exposes skill, agent, model or tool names, and it never answers
questions itself: a chosen prompt is sent, as written, to the Business Orchestrator (the same path as typed text).

  home       [--persona P] [--account A] [--admin]              6 prompts for the global front door + Explore categories
  menu       --capability ID [--persona P] [--account A] [--more]  Tier 1 (6 primary) and, with --more, Tier 2 grouped by category
  explore    [--category C] [--admin]                           capabilities by Explore category (Growth, Sales, …)
  hub        --hub sales|growth [--persona P] [--account A]     domain hub for a slash command such as /sales
  recommend  [--persona P] [--account A] [--capability ID] [--previous TEXT] [--contract C.json] [--signals S.json] [--limit 5]
             Tier 3 contextual prompts (only when a real signal exists) + persona + workflow next steps; small and ranked
  followups  --after TEXT [--contract C.json] [--signals S.json] [--account A] [--limit 5]
  resolve    --text TEXT [--account A] [--competitor C] [--opportunity O] [--meeting M] [--industry I]
  route      --text TEXT [--capability ID]                      orchestration path via agent_planner.py (for tests and slash commands)
All outputs are JSON. Context variables: account, opportunity, competitor, meeting, industry, time_period.
"""
import argparse, glob, json, os, re, subprocess, sys
import yaml
HERE = os.path.dirname(os.path.abspath(__file__)); CAT = os.path.join(os.path.dirname(HERE), "references", "starter-prompts")
IDX = yaml.safe_load(open(os.path.join(CAT, "_index.yaml"))); PERS = yaml.safe_load(open(os.path.join(CAT, "_personas.yaml")))
CAPS = {}
for f in sorted(glob.glob(os.path.join(CAT, "*.yaml"))):
    if os.path.basename(f).startswith("_"): continue
    c = yaml.safe_load(open(f))["capability"]; CAPS[c["id"]] = c
# ---------------- template resolution ----------------
OPT = re.compile(r"\[\[(.*?)(?:\|(.*?))?\]\]")
def resolve(text, ctx):
    def opt(m):
        with_, without = m.group(1), m.group(2) or ""
        names = re.findall(r"\{(\w+)\}", with_)
        return with_.format(**{n: ctx[n] for n in names}) if names and all(ctx.get(n) for n in names) else without
    out = OPT.sub(opt, text)
    out = re.sub(r"\{(\w+)\}", lambda m: ctx.get(m.group(1)) or m.group(0), out)
    return re.sub(r"\s{2,}", " ", out).replace(" .", ".").replace(" ?", "?").strip()
ROUTE_OVERRIDE = {p["text"]: p["routes_to_capability"] for c in CAPS.values() for p in c["primary_prompts"] if p.get("routes_to_capability")}
def card(text, cap, ctx, category=None, why=None, tier=None):
    cap = ROUTE_OVERRIDE.get(text, cap); c = CAPS[cap]
    d = {"prompt": resolve(text, ctx), "capability": c["name"], "category": category}
    if why: d["why"] = why
    if tier: d["tier"] = tier
    d["_route"] = {"capability_id": cap}                    # internal; UIs must not display keys starting with "_"
    return d
def visible(cap, admin): return admin or CAPS[cap]["audience"] != "administrators"
def persona_primary(cap, persona):
    c = CAPS[cap]; pp = (c.get("persona_prompts") or {}).get(persona or "", [])
    base = [(p["text"], p["category"]) for p in c["primary_prompts"]]
    if not pp: return base
    # persona prompts lead, then defaults; still exactly 6
    pp_c = [(t, next((p["category"] for p in c["primary_prompts"] + c["additional_prompts"] if p["text"] == t), "Discover")) for t in pp]
    seen, out = set(), []
    for t, k in pp_c + base:
        if t not in seen: seen.add(t); out.append((t, k))
    return out[:6]
def home(persona, ctx, admin):
    items = PERS[persona]["home"] if persona in PERS else IDX["global_home"]
    cards = [card(CAPS[i["capability"]]["primary_prompts"][i["primary_index"]]["text"], i["capability"], ctx, CAPS[i["capability"]]["primary_prompts"][i["primary_index"]]["category"]) for i in items if visible(i["capability"], admin)]
    return {"title": "What would you like to do?", "persona": PERS.get(persona, {}).get("label"), "prompts": cards[:6],
            "explore": [{"category": e, "capabilities": [CAPS[k]["name"] for k in CAPS if CAPS[k]["domain"] == e and visible(k, admin)]} for e in IDX["explore_categories"]],
            "explore_label": "Explore capabilities", "hint": "…or type /growth in any chat."}
def menu(cap, persona, ctx, more):
    c = CAPS[cap]
    out = {"capability": c["name"], "description": c["description"], "command": c["slash_command"],
           "prompts": [card(t, cap, ctx, k) for t, k in persona_primary(cap, persona)], "example_outcomes": c["example_outcomes"]}
    if more:
        groups = {}
        for p in c["additional_prompts"]: groups.setdefault(p["category"], []).append(card(p["text"], cap, ctx, p["category"]))
        out["more_prompts"] = {k: groups[k] for k in IDX["prompt_categories"] if k in groups}
    else:
        out["more_label"] = f"More prompts ({len(c['additional_prompts'])})"
    return out
# ---------------- Tier 3: contextual prompts from real signals ----------------
def signals_from_contract(C):
    s = {"account": C.get("dashboard", {}).get("entity_name")}
    s["threads_accelerating"] = [t["competitor"] for t in C.get("competitive_threads", []) if t.get("status") == "active" and str(t.get("momentum", "")).startswith("accel") and t.get("thread_type") != "displacement_opportunity"]
    s["displacement_opportunities"] = [t["competitor"] for t in C.get("competitive_threads", []) if t.get("status") == "active" and t.get("thread_type") == "displacement_opportunity" and t.get("opportunity_level") in ("High", "Medium")]
    s["anomalies"] = [i["label"] for i in C.get("insights", []) if i.get("anomaly")]
    s["champion_weakening"] = [r["role"] for r in C.get("relationships", []) if r.get("trend") == "down" and r.get("influence", 0) >= 0.6]
    s["intent_surge"] = bool((C.get("marketing") or {}).get("intent", {}).get("surge"))
    s["probability_drops"] = [r["label"].split(":")[0] for r in C.get("risks", []) if r.get("category") == "Pipeline" and "probability fell" in r.get("label", "")]
    s["margin_compression"] = any(r.get("id") == "R-FIN-MARGIN" for r in C.get("risks", []))
    s["pending_decisions"] = [d["question"] for d in C.get("decisions", []) if d.get("status") != "decided"]
    s["changes"] = len(C.get("changes", []))
    return s
RULES = [  # (signal key, capability, template, why)
 ("threads_accelerating", "threads", "Investigate the {competitor} threat.", "{competitor} thread is accelerating"),
 ("threads_accelerating", "threads", "Which opportunities does {competitor} affect?", "{competitor} thread is accelerating"),
 ("threads_accelerating", "threads", "Prepare a competitive response to {competitor}.", "{competitor} thread is accelerating"),
 ("displacement_opportunities", "competition", "Find a displacement opportunity against {competitor}.", "{competitor} is weakening"),
 ("anomalies", "bi", "Explain the {item}.", "an anomaly was detected"),
 ("champion_weakening", "relationships", "Build a plan to re-engage the {item}.", "a key relationship is weakening"),
 ("intent_surge", "marketing", "Act on the buying intent in [[{account}|this account]].", "buying intent is surging"),
 ("probability_drops", "deal", "Review why {item} lost momentum.", "deal probability fell"),
 ("margin_compression", "financial", "Explain the account margin decline.", "account margin is compressing"),
 ("pending_decisions", "decision", "Help me make the pending decision.", "a decision is awaiting you"),
 ("changes", "account", "Show me what changed[[ in {account}]].", "there are new changes since the last snapshot"),
]
def contextual(sig, ctx):
    out = []
    for key, cap, tpl, why in RULES:
        v = sig.get(key)
        if not v: continue
        items = v if isinstance(v, list) else [None]
        for it in items[:1]:
            c2 = dict(ctx); c2.setdefault("account", sig.get("account"))
            if key.startswith("threads") or key.startswith("displacement"): c2["competitor"] = it
            t = tpl.replace("{item}", (it or "").replace("Revenue anomaly in ", "revenue anomaly in ") if it else "")
            w = why.replace("{competitor}", it or "")
            out.append(card(t, cap, c2, "Investigate" if cap in ("threads", "bi", "deal", "financial") else "Act", w, "contextual"))
    return out
NEXT = {"Discover": ["Analyze", "Investigate"], "Analyze": ["Investigate", "Decide"], "Investigate": ["Decide", "Act"], "Decide": ["Prepare", "Act"], "Prepare": ["Act"], "Act": ["Monitor"], "Monitor": ["Investigate", "Act"]}
def find_prompt(text):
    t = text.strip().lower()
    for k, c in CAPS.items():
        for p in c["primary_prompts"] + c["additional_prompts"]:
            if resolve(p["text"], {}).lower() == t or re.sub(r"\[\[.*?\]\]", "", p["text"]).lower().replace("  ", " ") == t: return k, p["category"]
        for f in c["follow_up_prompts"]:
            if resolve(f, {}).lower() == t: return k, None
    return None, None
def followups(after, sig, ctx, limit):
    cap, catg = find_prompt(after)
    out = contextual(sig, ctx) if sig else []
    if cap:
        for f in CAPS[cap]["follow_up_prompts"]:
            k, kc = find_prompt(resolve(f, {}))
            out.append(card(f, k or cap, ctx, kc, f"follows {CAPS[cap]['name'].lower()}", "follow-up"))
        for nxt in NEXT.get(catg or "", []):
            p = next((p for p in CAPS[cap]["additional_prompts"] if p["category"] == nxt), None)
            if p: out.append(card(p["text"], cap, ctx, nxt, f"next step: {nxt.lower()}", "workflow"))
    seen, res = {after.strip().lower()}, []
    for c in out:
        if c["prompt"].lower() not in seen: seen.add(c["prompt"].lower()); res.append(c)
    return {"after": after, "capability": CAPS[cap]["name"] if cap else None, "prompts": res[:limit]}
def recommend(persona, ctx, cap, previous, sig, limit, admin):
    ctxl, used = [], set()                                  # at most 3 contextual prompts, one per capability
    for c in (contextual(sig, ctx) if sig else []):
        if c["_route"]["capability_id"] not in used and len(ctxl) < 3: used.add(c["_route"]["capability_id"]); ctxl.append(c)
    out = ctxl
    if previous: out += followups(previous, None, ctx, 3)["prompts"]
    if cap: out += [card(t, cap, ctx, k, "current capability", "primary") for t, k in persona_primary(cap, persona)[:3]]
    out += home(persona, ctx, admin)["prompts"]
    seen, res = {(previous or "").lower()}, []
    for c in out:
        if c["prompt"].lower() not in seen and visible(c["_route"]["capability_id"], admin): seen.add(c["prompt"].lower()); res.append(c)
    return {"prompts": res[:limit], "contextual_included": any(c.get("tier") == "contextual" for c in res[:limit])}
def route(text, cap):
    planner = None
    d = HERE
    for _ in range(4):
        cand = glob.glob(os.path.join(d, "skills", "business-orchestrator", "scripts", "agent_planner.py")) or glob.glob(os.path.join(d, "business-orchestrator", "scripts", "agent_planner.py"))
        if cand: planner = cand[0]; break
        d = os.path.dirname(d)
    args = [sys.executable, planner, text] + (["--capability", cap] if cap else [])
    r = subprocess.run(args, capture_output=True, text=True); p = json.loads(r.stdout)
    skills = sorted({s for st in p["steps"] for s in st.get("skills", [])})
    return {"text": text, "intent": p["intent"], "skills": skills, "agents": p["agents"], "via": "business-orchestrator"}
ap = argparse.ArgumentParser(); ap.add_argument("cmd")
for k in ["persona", "account", "capability", "previous", "contract", "signals", "after", "text", "competitor", "opportunity", "meeting", "industry", "category", "hub", "time_period"]: ap.add_argument("--" + k)
ap.add_argument("--more", action="store_true"); ap.add_argument("--admin", action="store_true"); ap.add_argument("--limit", type=int, default=5)
a = ap.parse_args()
ctx = {k: getattr(a, k) for k in ["account", "competitor", "opportunity", "meeting", "industry", "time_period"] if getattr(a, k)}
sig = signals_from_contract(json.load(open(a.contract))) if a.contract else (json.load(open(a.signals)) if a.signals else None)
if sig and sig.get("account") and "account" not in ctx: ctx["account"] = sig["account"]
if a.persona and a.persona not in PERS: print(json.dumps({"error": f"unknown persona {a.persona}", "personas": list(PERS)})); sys.exit(2)
if a.capability and a.capability not in CAPS: print(json.dumps({"error": f"unknown capability {a.capability}"})); sys.exit(2)
if a.cmd == "home": res = home(a.persona, ctx, a.admin)
elif a.cmd == "menu":
    if CAPS[a.capability]["audience"] == "administrators" and not a.admin: res = {"error": "not available"}
    else: res = menu(a.capability, a.persona, ctx, a.more)
elif a.cmd == "explore": res = {e["category"]: e["capabilities"] for e in home(None, ctx, a.admin)["explore"] if not a.category or e["category"] == a.category}
elif a.cmd == "hub":
    h = IDX["hubs"][a.hub]
    res = home(a.persona, ctx, a.admin) if not h["capabilities"] else {"title": h["name"], "description": h["description"],
          "prompts": [card(persona_primary(c, a.persona)[0][0], c, ctx, persona_primary(c, a.persona)[0][1]) for c in h["capabilities"]][:6], "capabilities": [CAPS[c]["name"] for c in h["capabilities"]]}
elif a.cmd == "recommend": res = recommend(a.persona, ctx, a.capability, a.previous, sig, a.limit, a.admin)
elif a.cmd == "followups": res = followups(a.after, sig, ctx, a.limit)
elif a.cmd == "resolve": res = {"text": resolve(a.text, ctx)}
elif a.cmd == "route": res = route(a.text, a.capability)
else: res = {"error": "unknown command"}
print(json.dumps(res, indent=1, ensure_ascii=False))
