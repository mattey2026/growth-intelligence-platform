#!/usr/bin/env python3
"""
account_plan_builder.py: integrated account plan (V7.1 Account Intelligence upgrade).

Assembles the 12 required sections from domain outputs. Every material conclusion carries a claim_type and
evidence references. A section with no evidence is emitted as {"status": "insufficient_evidence", "needed": [...]}
instead of being filled with generic text.
Sections: 1 business_context · 2 financial_position · 3 strategic_priorities · 4 marketing_engagement · 5 customer_footprint ·
6 relationship_map · 7 competitive_landscape · 8 active_competitive_threads · 9 opportunities · 10 risks · 11 swot · 12 recommended_actions
USAGE: account_plan_builder.py --account A [--profile p.json] [--financial fi.json] [--marketing mk.json] [--threads th.json] [--correlation cd.json]
          [--opportunities op.json] [--twin twin.json] [--bundle bundle.json] [--out plan.json] [--md plan.md]
"""
import argparse, json, os
ap = argparse.ArgumentParser()
for k in ["account", "profile", "financial", "marketing", "threads", "correlation", "opportunities", "twin", "bundle", "out", "md"]: ap.add_argument("--" + k)
a = ap.parse_args()
J = lambda f: json.load(open(f)) if f and os.path.exists(f) else None
pr, fi, mk, th, cd, op, tw, B = J(a.profile), J(a.financial), J(a.marketing), J(a.threads) or [], J(a.correlation), J(a.opportunities), J(a.twin), J(a.bundle) or {}
A = a.account; th = [t for t in th if t.get("account_id") == A]
pick = lambda k: [r for r in B.get(k, []) if r.get("account_id", A) == A]
import re as _re
def _ev(e):
    """Normalize evidence to {source[, date]} so the evidence validator can check it; ids stay ids."""
    if isinstance(e, dict): return e
    s = str(e); m = _re.search(r"\((\d{4}-\d{2}-\d{2})\)\s*$", s)
    return {"source": s[:m.start()].strip() if m else s, **({"date": m.group(1)} if m else {})}
C = lambda text, ct, ev: {"text": text, "claim_type": ct, "evidence": [_ev(x) for x in (ev if isinstance(ev, list) else [ev]) if x not in (None, "")]}
INS = lambda *need: {"status": "insufficient_evidence", "needed": list(need)}
S = {}
S["1_business_context"] = ([C(f"Seller context: {pr['business_model']['value']} · {pr['industry']['seller_industry']}", "FACT", "business_context_profile")] if pr else []) + \
    [C(x["text"], "FACT", x["source"]) for x in pick("public_profile")] or INS("business context profile or public company profile")
if fi:
    last = fi["periods"][-1]; m = fi["metrics"][last]
    def fmt(x):
        u, val = x["unit"], x["value"]
        if u == "ratio": return f"{val:.1%}"
        if u in ("x",): return f"{val:.2f}×"
        if u == "days": return f"{val:.0f} days"
        return f"{val:,.0f} {u}" if u not in ("currency",) else f"{val:,.0f}"
    items = [C(f"{k.replace('_', ' ').capitalize()} {last}: {fmt(m[k])}" + ("" if m[k]["formula"] == "reported" else f" ({m[k]['formula']})"), m[k]["claim_type"],
               [f"{i['source']} ({i['source_date']})" for i in m[k]["inputs"]]) for k in ("revenue", "revenue_growth", "gross_margin", "operating_margin", "fcf_margin") if k in m]
    items += [C(f"Not available: {x['metric']} (needs {', '.join(x['needs'])})", "FACT", "financial_intel.py missing-data check") for x in fi["missing"].get(last, [])[:6]]
    S["2_financial_position"] = items
else: S["2_financial_position"] = INS("customer financial statements or public filings")
sp = [C(e["text"], "FACT", f"{e['source']} ({e.get('source_date')})") for e in pick("initiatives") if e.get("source")]
sp += [C(s["text"], s["claim_type"], s["evidence"] if isinstance(s["evidence"], list) and s["evidence"] and isinstance(s["evidence"][0], str) else [str(x) for x in s["evidence"]]) for s in (fi or {}).get("signals", []) if s["kind"] in ("m_and_a", "guidance", "restructuring", "cost_transformation")]
S["3_strategic_priorities"] = sp or INS("stated customer priorities (filings, investor materials, executive statements)")
mu = (mk or {}).get("units", {}).get(A)
S["4_marketing_engagement"] = [C(f"Engagement {mu['engagement_score']['direction']} ({mu['engagement_score']['previous']} → {mu['engagement_score']['current']})", "FACT", mu["sources"]),
    C(f"Executive engagement: {mu['executive_engagement']['current']} touches ({', '.join(mu['executive_engagement']['roles']) or 'none'})", "FACT", mu["executive_engagement"]["evidence"]) if mu.get("executive_engagement") else None,
    C(f"Buying intent: {mu['buying_intent']['current']} signals{' — SURGE' if mu['buying_intent']['surge'] else ''}", "FACT", mu["buying_intent"]["evidence"])] if mu else INS("marketing engagement signals for the account")
if isinstance(S["4_marketing_engagement"], list): S["4_marketing_engagement"] = [x for x in S["4_marketing_engagement"] if x]
fp = pick("footprint") + pick("contracts")
S["5_customer_footprint"] = [C(f"{f.get('offering') or f.get('scope')}: {f.get('value', 'value n/a')}", "FACT", f.get("source", "CRM")) for f in fp] or INS("existing contracts / install base")
ct = pick("contacts")
S["6_relationship_map"] = [C(f"{c.get('name', c.get('contact_id'))} — {c.get('role')}: {c.get('relationship_strength', 'unknown')}{' (champion)' if str(c.get('champion')).lower() in ('yes', 'true') else ''}", "FACT", c.get("source", "CRM")) for c in ct] or INS("contacts with roles and relationship strength")
comps = sorted({t["competitor_id"] for t in th} | {c.get("competitor") for c in pick("competitors") if c.get("competitor")})
S["7_competitive_landscape"] = [C(f"{c} present", "FACT", [e["source"] for t in th if t["competitor_id"] == c for e in t.get("evidence", [])][:3] or ["competitor record"]) for c in comps] or INS("competitor presence data")
S["8_active_competitive_threads"] = [C(f"{t['title']}: {t['momentum']}, risk {t['risk_level']}, {t['signal_count']} signals, confidence {t['confidence']}", "INFERENCE", [e["signal_id"] for e in t.get("evidence", [])]) for t in th if t.get("status") != "resolved"] or INS("competitive signals (none recorded)")
ops = (op or {}).get("opportunities", [])
S["9_opportunities"] = [C(f"{o['opportunity']} — value: {('%s–%s (%s)' % (format(o['estimated_value']['low'], ','), format(o['estimated_value']['high'], ','), o['estimated_value']['claim_type'])) if o['estimated_value'].get('high') else 'UNSIZED'}; confidence {o['confidence']}",
                          "HYPOTHESIS", [str(e.get("detail")) for e in o["evidence"]][:4]) for o in ops] or INS("whitespace, signals or patterns to build opportunities")
risks = [C(p["text"], "HYPOTHESIS", p["supporting_evidence"]) for p in (cd or {}).get("patterns", []) if p["pattern_id"] in ("P3", "P4") and p["status"] != "not_detected"]
risks += [C(f"{t['competitor_id']} threat {t['risk_level']} ({t['momentum']})", "INFERENCE", [t["thread_id"]]) for t in th if t.get("risk_level") in ("High", "Medium") and t.get("thread_type") != "displacement_opportunity"]
risks += [C(f"Financial signal: {s['text']}", s["claim_type"], [s["signal_id"]]) for s in (fi or {}).get("signals", []) if s["kind"] in ("revenue_decline", "margin_pressure", "investment_reduction", "cash_generation_weakening")]
S["10_risks"] = risks or INS("risk signals (none detected in the available domains)")
sw = {"strengths": [x for x in S["6_relationship_map"] if isinstance(S["6_relationship_map"], list) and "Strong" in x["text"]][:3] if isinstance(S["6_relationship_map"], list) else [],
      "weaknesses": [x for x in (S["6_relationship_map"] if isinstance(S["6_relationship_map"], list) else []) if "Weak" in x["text"]][:3],
      "opportunities": (S["9_opportunities"][:3] if isinstance(S["9_opportunities"], list) else []), "threats": (S["10_risks"][:3] if isinstance(S["10_risks"], list) else [])}
S["11_swot"] = {k: v or INS(f"evidence for {k}") for k, v in sw.items()}
acts = [C(t["recommended_actions"][0]["action"], "RECOMMENDATION", [t["thread_id"]]) for t in th if t.get("recommended_actions")]
acts += [C(o["recommended_action"]["text"] + f" — {o['opportunity']}", "RECOMMENDATION", [o["source_type"]]) for o in ops[:3]]
S["12_recommended_actions"] = acts or INS("opportunities or risks to act on")
def flat(x):
    if isinstance(x, list): return x
    if isinstance(x, dict) and "status" not in x: return [i for v in x.values() for i in flat(v)]
    return []
concl = [c for s in S.values() for c in flat(s)]
res = {"account": A, "sections": S, "section_status": {k: ("insufficient_evidence" if isinstance(v, dict) and v.get("status") else "ok") for k, v in S.items()},
       "conclusions": len(concl), "conclusions_without_evidence": sum(1 for c in concl if not c["evidence"] or c["evidence"] == [None]),
       "claim_types": {t: sum(1 for c in concl if c["claim_type"] == t) for t in sorted({c["claim_type"] for c in concl})}}
print(json.dumps(res, indent=1, default=str))
if a.out: json.dump(res, open(a.out, "w"), indent=1, default=str)
if a.md:
    L = [f"# Account plan — {A}", ""]
    for k, v in S.items():
        L.append(f"## {k.split('_', 1)[0]}. {k.split('_', 1)[1].replace('_', ' ').title()}")
        if isinstance(v, dict) and v.get("status"): L.append(f"*Insufficient evidence — needed: {', '.join(v['needed'])}*")
        elif isinstance(v, dict):
            for q, items in v.items():
                L.append(f"**{q.title()}:** " + ("; ".join(i["text"] for i in items) if isinstance(items, list) else f"insufficient evidence ({', '.join(items['needed'])})"))
        else:
            ev_txt = lambda c: "; ".join(f"{e.get('source')}" + (f" ({e['date']})" if e.get("date") else "") for e in c["evidence"])
            L += [f"- [{c['claim_type']}] {c['text']}  \n  <sub>evidence: {ev_txt(c)[:240]}</sub>" for c in v]
        L.append("")
    open(a.md, "w").write("\n".join(L))
