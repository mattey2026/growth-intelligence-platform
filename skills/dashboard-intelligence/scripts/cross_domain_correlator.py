#!/usr/bin/env python3
"""
cross_domain_correlator.py: Growth Signal Orchestrator V7.1 cross-domain patterns.

  P1 marketing_to_growth       material engagement rise + executive engagement + relevant initiative        → expansion HYPOTHESIS
  P2 financial_to_growth       margin pressure + cost transformation/pressure + technology investment      → transformation-opportunity HYPOTHESIS
  P3 financial_to_risk         revenue decline + margin decline + reduced investment                        → account-risk HYPOTHESIS
  P4 competitive_displacement  competitor activity + RFP + champion weakening                               → displacement thread (create/update)
  P5 compound_growth           positive signals from ≥3 independent domains in the window                   → cross-functional growth HYPOTHESIS
Each pattern reports: detected | emerging (partial) | not detected, supporting evidence, a confidence that is capped
when components are missing, the missing evidence, the memory write, and the agent it routes to. Output is never a FACT.

USAGE: cross_domain_correlator.py --account A [--marketing mk.json] [--financial fi.json] [--threads threads.json]
          [--relationship rel.json] [--initiatives init.json] [--memory-db mem.db] [--out out.json]
"""
import sys
import argparse, json, os, subprocess, hashlib
ap = argparse.ArgumentParser()
for k in ["account", "marketing", "financial", "threads", "relationship", "initiatives", "memory-db", "out", "asof"]: ap.add_argument("--" + k)
a = ap.parse_args()
J = lambda f: json.load(open(f)) if f and os.path.exists(f) else None
mk, fi, th, rel, ini = J(a.marketing), J(a.financial), J(a.threads) or [], J(a.relationship) or [], J(a.initiatives) or []
acct = a.account
mu = (mk or {}).get("units", {}).get(acct)
fs = {s["kind"]: s for s in (fi or {}).get("signals", [])}
th = [t for t in th if t.get("account_id") == acct]
rel = [r for r in rel if r.get("account_id") == acct]
ini = [i for i in ini if i.get("account_id") == acct]
domains_available = {"marketing": mk is not None and mu is not None, "financial": fi is not None, "competitive": bool(th) or a.threads is not None,
                     "relationship": a.relationship is not None, "market_initiatives": a.initiatives is not None}
P = []
def pattern(pid, name, comps, route, out_type, text):
    have = [c for c in comps if c[1]]; miss = [c[0] for c in comps if not c[1]]
    k = len(have)
    status = "detected" if k == len(comps) else "emerging" if k >= 2 else "not_detected"
    conf = round(min(0.85, 0.2 + 0.2 * k) * (1.0 if not miss else 0.7), 2) if k else 0.0
    ev = [e for c in have for e in (c[2] if isinstance(c[2], list) else [c[2]])]
    P.append({"pattern_id": pid, "name": name, "status": status, "claim_type": "HYPOTHESIS" if status != "not_detected" else None, "output_type": out_type,
              "text": text if status != "not_detected" else None, "supporting_evidence": ev, "components_present": [c[0] for c in have], "missing_evidence": miss,
              "confidence": conf, "route_to": route if status != "not_detected" else None,
              "caution": "Correlated signals, not proof: validate with the account team before acting" if status != "not_detected" else None})
# P1
eng = mu and mu["engagement_score"]["material"] and mu["engagement_score"]["direction"] in ("up", "new engagement")
ex = mu and mu.get("executive_engagement") and mu["executive_engagement"]["current"] > 0
topics = (mu or {}).get("topics", [])
rel_init = [i for i in ini if any(t in (i.get("topic") or "").lower() or (i.get("topic") or "").lower() in t for t in topics)]
pattern("P1", "marketing_to_growth", [("material engagement increase", eng, [f"AccountEngagement:{acct}"] if eng else []),
        ("executive engagement", ex, (mu or {}).get("executive_engagement", {}).get("evidence", []) if ex else []),
        ("relevant customer initiative", bool(rel_init), [i.get("initiative_id") for i in rel_init])],
        ["opportunity-agent", "account-intelligence-agent"], "expansion_hypothesis", f"Expansion hypothesis at {acct}: rising engagement from executives around {', '.join(topics) or 'engaged topics'}")
# P2
pattern("P2", "financial_to_growth", [("margin pressure", "margin_pressure" in fs, fs.get("margin_pressure", {}).get("signal_id")),
        ("cost transformation or cost pressure", any(k in fs for k in ("cost_transformation", "cost_pressure", "restructuring")), [fs[k]["signal_id"] for k in ("cost_transformation", "cost_pressure", "restructuring") if k in fs]),
        ("technology investment", "technology_investment" in fs, fs.get("technology_investment", {}).get("signal_id"))],
        ["opportunity-agent", "solution-architect-agent"], "transformation_opportunity_hypothesis", f"Transformation opportunity at {acct}: margin pressure with an active cost and technology agenda")
# P3
pattern("P3", "financial_to_risk", [("revenue decline", "revenue_decline" in fs, fs.get("revenue_decline", {}).get("signal_id")),
        ("margin decline", "margin_pressure" in fs, fs.get("margin_pressure", {}).get("signal_id")),
        ("reduced investment", "investment_reduction" in fs, fs.get("investment_reduction", {}).get("signal_id"))],
        ["customer-growth-agent", "executive-decision-agent"], "account_risk_hypothesis", f"Account risk at {acct}: shrinking revenue, margins and investment may cut discretionary spend")
# P4
act = [t for t in th if t.get("thread_type") in ("displacement_risk", "competitive_pursuit") and t.get("status") != "resolved"]
kinds = {c["kind"] for t in act for c in t.get("chronology", [])}
champ = any(r.get("kind") == "champion_weakening" for r in rel) or "champion_weakening" in kinds
pattern("P4", "competitive_displacement", [("competitor activity", bool(act), [t["thread_id"] for t in act]),
        ("RFP or shortlist", bool(kinds & {"rfp_participation", "competitor_shortlisted"}), [t["thread_id"] for t in act if {c["kind"] for c in t.get("chronology", [])} & {"rfp_participation", "competitor_shortlisted"}]),
        ("champion weakening", champ, [r.get("signal_id") for r in rel if r.get("kind") == "champion_weakening"])],
        ["competitive-thread-agent", "deal-strategy-agent", "relationship-agent"], "displacement_thread", f"Competitive displacement risk at {acct}")
# P5: independent domains with a positive signal
pos = {"marketing": bool(eng or (mu and mu["buying_intent"]["current"] > 0)),
       "financial": any(k in fs for k in ("growth_acceleration", "technology_investment", "operating_leverage", "cash_generation_improving", "m_and_a", "margin_pressure")),
       "competitive": any(t.get("thread_type") == "displacement_opportunity" for t in th),
       "relationship": any(r.get("kind") in ("new_sponsor", "sponsor_strengthening", "exec_access_gained") for r in rel),
       "market_initiatives": bool(ini)}
doms = [d for d, v in pos.items() if v]
comps = [(d, pos[d], [d]) for d in pos]
k = len(doms)
P.append({"pattern_id": "P5", "name": "compound_growth", "status": "detected" if k >= 3 else "emerging" if k == 2 else "not_detected",
          "claim_type": "HYPOTHESIS" if k >= 2 else None, "output_type": "cross_functional_growth_hypothesis",
          "text": f"Cross-functional growth hypothesis at {acct}: aligned signals in {', '.join(doms)}" if k >= 2 else None,
          "supporting_evidence": doms, "components_present": doms, "missing_evidence": [d for d in pos if not pos[d]],
          "confidence": round(min(0.85, 0.15 * k + 0.1), 2) if k >= 2 else 0.0, "route_to": ["opportunity-agent", "executive-decision-agent"] if k >= 2 else None,
          "caution": "Independent domains agreeing raises confidence, but each signal still needs validation" if k >= 2 else None})
res = {"account": acct, "domains_available": domains_available, "patterns": P, "detected": [p["pattern_id"] for p in P if p["status"] == "detected"],
       "emerging": [p["pattern_id"] for p in P if p["status"] == "emerging"],
       "data_gaps": [d for d, v in domains_available.items() if not v]}
if a.memory_db:
    objs = [{"obj_id": "CDP-" + hashlib.sha1(f"{acct}{p['pattern_id']}{p['components_present']}".encode()).hexdigest()[:10], "obj_type": "CrossDomainPattern", "account_id": acct,
             "observed_at": a.asof or __import__("datetime").date.today().isoformat(), "source": "cross_domain_correlator.py", "confidence": p["confidence"], "claim_type": "HYPOTHESIS",
             "data": p} for p in P if p["status"] != "not_detected"]
    if objs:
        f = (a.out or "/tmp/cd") + ".objs.json"; json.dump(objs, open(f, "w"), default=str)
        r = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "memory_graph.py"), a.memory_db, "obj-put", f], capture_output=True, text=True)
        res["memory"] = json.loads(r.stdout) if r.stdout.startswith("{") else {"error": r.stdout or r.stderr}
print(json.dumps(res, indent=1, default=str))
if a.out: json.dump(res, open(a.out, "w"), indent=1, default=str)
