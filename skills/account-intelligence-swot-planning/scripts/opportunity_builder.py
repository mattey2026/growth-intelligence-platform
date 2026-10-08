#!/usr/bin/env python3
"""
opportunity_builder.py: cross-domain opportunity discovery (V7.1).

Consumes: whitespace, financial signals, marketing intent, competitive threads, product usage, relationships,
market initiatives, existing footprint, pricing benchmarks, contracts, historical outcomes, and correlator patterns.
Every opportunity has: opportunity, why_now, business_driver, evidence, estimated_value, confidence,
competitive_context, stakeholders, recommended_action, risks, missing_evidence.
estimated_value is either a sourced range with its basis and claim_type, or {"status": "unsized", ...}: a value is
never invented. A whitespace estimate is an INTERNAL ESTIMATE, not a fact.
USAGE: opportunity_builder.py --account A --bundle bundle.json [--correlation cd.json] [--threads th.json] [--marketing mk.json]
          [--financial fi.json] [--model B2B|B2C|B2B2C] [--out out.json]
bundle keys (all optional): whitespace[], usage[], contacts[], contracts[], pricing[], outcomes[], footprint[], initiatives[]
"""
import argparse, json, os
ap = argparse.ArgumentParser()
for k in ["account", "bundle", "correlation", "threads", "marketing", "financial", "out"]: ap.add_argument("--" + k)
ap.add_argument("--model", default="B2B"); a = ap.parse_args()
J = lambda f: json.load(open(f)) if f and os.path.exists(f) else None
B = J(a.bundle) or {}; cd = J(a.correlation) or {"patterns": []}; th = [t for t in (J(a.threads) or []) if t.get("account_id") == a.account]
mk = J(a.marketing); fi = J(a.financial); acct = a.account
pick = lambda k: [r for r in B.get(k, []) if r.get("account_id", acct) == acct]
ws, us, ct, cs, pr, oc, ini = pick("whitespace"), pick("usage"), pick("contacts"), pick("contracts"), pick("pricing"), pick("outcomes"), pick("initiatives")
mu = (mk or {}).get("units", {}).get(acct, {})
champs = [c for c in ct if str(c.get("champion", "")).lower() in ("yes", "true") or c.get("relationship_strength") == "Strong"]
wr = {}
for o in oc:
    wr.setdefault(o.get("offering"), []).append(1 if o.get("outcome") == "won" else 0)
OPP = []
def stakeholders_for(off=None):
    return [{"contact_id": c.get("contact_id"), "role": c.get("role"), "strength": c.get("relationship_strength")} for c in ct][:5]
def comp_ctx(off=None):
    act = [t for t in th if t.get("status") != "resolved"]
    return [{"thread_id": t["thread_id"], "competitor": t["competitor_id"], "type": t["thread_type"], "risk": t.get("risk_level"), "momentum": t.get("momentum")} for t in act] or "no active competitive threads recorded"
def conf_adj(base, off):
    h = wr.get(off)
    return (round(min(0.9, base * (0.6 + 0.8 * sum(h) / len(h))), 2), f"historical win rate {sum(h)}/{len(h)} for {off}") if h and len(h) >= 5 else (round(base, 2), "no reliable win/loss history for this offering (need ≥5)")
for w in ws:
    miss = []
    if not mu: miss.append("marketing engagement for the account")
    if not fi: miss.append("customer financial context")
    if not champs: miss.append("a champion or strong relationship")
    c, basis = conf_adj(0.35 + 0.1 * (w.get("relationship_access") == "Strong") + 0.1 * bool(mu.get("buying_intent", {}).get("current")) + 0.05 * bool(fi), w.get("offering"))
    OPP.append({"opportunity": f"{w.get('offering')} for {acct}", "source_type": "whitespace", "why_now": ("buying intent observed" if mu.get("buying_intent", {}).get("current") else "whitespace gap; no timing trigger observed"),
        "business_driver": w.get("driver") or "not documented — confirm with the customer",
        "evidence": [{"type": "INTERNAL_ESTIMATE", "source": w.get("source", "whitespace analysis"), "detail": f"potential {w.get('potential')}"}] + ([{"type": "FACT", "source": "marketing", "detail": f"intent {mu['buying_intent']['types']}"}] if mu.get("buying_intent", {}).get("current") else []),
        "estimated_value": ({"low": round(w["estimated_value"] * 0.7), "high": w["estimated_value"], "basis": "internal whitespace estimate (upper) with 30% realization haircut (lower)", "claim_type": "INTERNAL_ESTIMATE"}
                            if w.get("estimated_value") else {"status": "unsized", "needed": ["scope and volume from the customer", "pricing benchmark"]}),
        "confidence": c, "confidence_basis": basis, "competitive_context": comp_ctx(), "stakeholders": stakeholders_for(), "recommended_action": {"text": "Validate the need with the sponsor; build a value hypothesis", "approval_required": False, "claim_type": "RECOMMENDATION"},
        "risks": [r for r in ["no timing trigger" if not mu.get("buying_intent", {}).get("current") else None, "competitor active" if isinstance(comp_ctx(), list) else None] if r], "missing_evidence": miss})
for p in cd.get("patterns", []):
    if p["status"] == "not_detected" or p["pattern_id"] in ("P3", "P4"): continue
    size = None
    fin_rev = (((fi or {}).get("metrics") or {}).get((fi or {}).get("periods", [None])[-1] or "", {}) or {}).get("revenue")
    OPP.append({"opportunity": p["text"], "source_type": f"pattern {p['pattern_id']} ({p['status']})", "why_now": f"signals aligned: {', '.join(p['components_present'])}",
        "business_driver": {"P1": "customer initiative with executive engagement", "P2": "margin pressure and cost/technology agenda", "P5": "multi-domain momentum"}.get(p["pattern_id"], p["name"]),
        "evidence": [{"type": "HYPOTHESIS", "source": "cross_domain_correlator", "detail": e} for e in p["supporting_evidence"]],
        "estimated_value": {"status": "unsized", "needed": ["scope definition with the customer", "comparable deal sizes", "pricing benchmark"],
                            "context": ({"customer_revenue": fin_rev["value"], "note": "context only — customer revenue is not deal size"} if fin_rev else None)},
        "confidence": p["confidence"], "confidence_basis": "pattern confidence (capped when components are missing)", "competitive_context": comp_ctx(), "stakeholders": stakeholders_for(),
        "recommended_action": {"text": "Test the hypothesis in a discovery conversation before sizing", "approval_required": False, "claim_type": "RECOMMENDATION"},
        "risks": ["correlated signals may not reflect a funded initiative"], "missing_evidence": p["missing_evidence"]})
for t in th:
    if t.get("thread_type") == "displacement_opportunity" and t.get("status") != "resolved":
        inc = [c for c in cs if c.get("competitor") == t["competitor_id"]]
        OPP.append({"opportunity": f"Displace {t['competitor_id']} at {acct}", "source_type": "competitive thread", "why_now": f"thread {t['thread_id']} momentum {t.get('momentum')}",
            "business_driver": "incumbent weakness", "evidence": [{"type": "FACT", "source": e.get("source"), "detail": e.get("signal_id")} for e in t.get("evidence", [])],
            "estimated_value": ({"low": round(inc[0]["value"] * 0.5), "high": inc[0]["value"], "basis": "incumbent contract value (known)", "claim_type": "FACT_BASED_RANGE"} if inc and inc[0].get("value")
                                else {"status": "unsized", "needed": ["incumbent contract value"]}),
            "confidence": t.get("confidence", 0.3), "confidence_basis": "thread confidence", "competitive_context": comp_ctx(), "stakeholders": stakeholders_for(),
            "recommended_action": {"text": "Qualify a displacement pursuit with the sponsor", "approval_required": False, "claim_type": "RECOMMENDATION"},
            "risks": ["incumbent recovery", "switching cost"], "missing_evidence": [] if inc else ["incumbent contract value and renewal date"]})
if a.model == "B2C":
    for o in OPP: o["opportunity"] = o["opportunity"].replace(" for ", " in segment ")
OPP.sort(key=lambda o: (-(o["estimated_value"].get("high") or 0), -o["confidence"]))
sized = [o for o in OPP if o["estimated_value"].get("high")]
res = {"account": acct, "model": a.model, "opportunities": OPP, "count": len(OPP), "sized": len(sized), "unsized": len(OPP) - len(sized),
       "sized_total_range": [sum(o["estimated_value"]["low"] for o in sized), sum(o["estimated_value"]["high"] for o in sized)] if sized else None,
       "note": "Only sized ranges with a stated basis are summed; unsized hypotheses are listed with the evidence needed to size them."}
print(json.dumps(res, indent=1, default=str))
if a.out: json.dump(res, open(a.out, "w"), indent=1, default=str)
