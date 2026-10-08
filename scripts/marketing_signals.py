#!/usr/bin/env python3
"""
marketing_signals.py: Marketing Intelligence engine (V7.1, deterministic).

1 ingest signals (JSON/CSV) → 2 normalize to the signal taxonomy (dedupe, parse dates, map synonyms, flag unknowns)
→ 3 account engagement change (current vs previous window) → 4 executive engagement (contact role)
→ 5 buying-intent signals and surges → 6 campaign→account links → 7 campaign→opportunity influence (touch before
opportunity creation, within the window; linear multi-touch share) → 8 correlation vs causation (influence is
CORRELATION unless the campaign carries a holdout/experiment result) → 9 evidence-backed commercial HYPOTHESES
→ 10 persist MarketingSignal / AccountEngagement / CampaignInfluence to Business Memory.

Business-model adaptation (--model): B2B = accounts and buying groups; B2C = segments/cohorts (no executive
engagement; intent = conversion events); B2B2C = partners/channels plus end-consumer demand.

USAGE: marketing_signals.py --signals s.json [--contacts c.json] [--opportunities o.json] [--campaigns m.json] [--initiatives i.json]
          [--model B2B|B2C|B2B2C] [--asof DATE] [--window-days 90] [--influence-days 120] [--memory-db mem.db] [--out out.json]
Signal fields: account_id (or segment/partner), occurred_at, type, source; optional contact_id, contact_role, campaign_id, topic, channel.
"""
import sys
import argparse, json, re, subprocess, os, hashlib
from datetime import datetime
TAX = {  # type → (category, weight)
 "ad_impression": ("awareness", 0.2), "website_visit": ("awareness", 0.5), "social_engagement": ("awareness", 0.5),
 "email_open": ("engagement", 0.5), "email_click": ("engagement", 1.0), "content_download": ("engagement", 1.5), "webinar_register": ("engagement", 1.0),
 "webinar_attend": ("engagement", 2.0), "event_attend": ("engagement", 2.5), "newsletter_subscribe": ("engagement", 0.5),
 "pricing_page_visit": ("intent", 3.0), "demo_request": ("intent", 5.0), "contact_sales": ("intent", 5.0), "third_party_intent": ("intent", 2.0),
 "competitor_comparison_view": ("intent", 2.5), "rfp_download": ("intent", 3.0), "trial_start": ("intent", 4.0), "add_to_cart": ("intent", 2.0), "purchase": ("conversion", 5.0),
 "exec_meeting": ("executive", 5.0), "exec_briefing_attend": ("executive", 4.0),
 "reference_call": ("advocacy", 3.0), "case_study_participation": ("advocacy", 3.0),
 "unsubscribe": ("negative", -1.0), "email_bounce": ("negative", -0.2), "complaint": ("negative", -2.0)}
SYN = {"open": "email_open", "click": "email_click", "download": "content_download", "webinar": "webinar_attend", "event": "event_attend",
       "visit": "website_visit", "pricing visit": "pricing_page_visit", "demo": "demo_request", "intent": "third_party_intent", "bombora": "third_party_intent",
       "exec meeting": "exec_meeting", "executive briefing": "exec_briefing_attend", "unsub": "unsubscribe"}
EXEC = r"\b(chief|ceo|cfo|cio|cto|coo|cdo|cmo|chro|president|evp|svp|vp|vice president|head of|managing director|general manager)\b"
CAUSAL = r"\b(caused|drove|because of|resulted in|led to|generated)\b"
ap = argparse.ArgumentParser()
for k in ["signals", "contacts", "opportunities", "campaigns", "initiatives", "memory-db", "out", "asof"]: ap.add_argument("--" + k)
ap.add_argument("--model", default="B2B"); ap.add_argument("--window-days", type=int, default=90); ap.add_argument("--influence-days", type=int, default=120)
a = ap.parse_args()
L = lambda f: (json.load(open(f)) if f and f.endswith(".json") else __import__("pandas").read_csv(f).to_dict("records")) if f else []
raw, contacts, opps, camps, inits = L(a.signals), L(a.contacts), L(a.opportunities), L(a.campaigns), L(a.initiatives)
asof = datetime.fromisoformat(a.asof) if a.asof else datetime.now()
role_of = {c["contact_id"]: c.get("role", "") for c in contacts}
unit = {"B2B": "account_id", "B2C": "segment", "B2B2C": "partner_id"}[a.model]
# ---- 1–2 ingest + normalize
norm, rejected, seen = [], [], set()
for s in raw:
    t = str(s.get("type", "")).strip().lower().replace("-", "_"); t = SYN.get(t.replace("_", " "), SYN.get(t, t))
    key_unit = s.get(unit) or s.get("account_id")
    if not key_unit or not s.get("occurred_at") or not s.get("source"):
        rejected.append({"signal": s.get("signal_id"), "reason": f"missing {unit}, occurred_at or source"}); continue
    try: when = datetime.fromisoformat(str(s["occurred_at"])[:19])
    except ValueError:
        rejected.append({"signal": s.get("signal_id"), "reason": "unparseable occurred_at"}); continue
    cat, w = TAX.get(t, ("unclassified", 0.0))
    role = s.get("contact_role") or role_of.get(s.get("contact_id"), "")
    if a.model != "B2C" and re.search(EXEC, str(role), re.I) and cat in ("engagement", "intent", "awareness"): cat_exec = True
    else: cat_exec = cat == "executive"
    dk = (key_unit, s.get("contact_id"), t, s.get("campaign_id"), when.date())
    if dk in seen:
        continue
    seen.add(dk)
    sid = s.get("signal_id") or "MS-" + hashlib.sha1(json.dumps(s, sort_keys=True, default=str).encode()).hexdigest()[:10]
    norm.append({"signal_id": sid, "unit": key_unit, "type": t, "category": cat, "weight": w, "executive": cat_exec and a.model != "B2C", "role": role,
                 "contact_id": s.get("contact_id"), "campaign_id": s.get("campaign_id"), "topic": (s.get("topic") or "").lower(), "at": when, "source": s["source"],
                 "classified": cat != "unclassified"})
dup = len(raw) - len(norm) - len(rejected)
W = a.window_days
cur = lambda dt: 0 <= (asof - dt).days < W          # dt = the signal's timestamp
prev = lambda dt: W <= (asof - dt).days < 2 * W
units = sorted({n["unit"] for n in norm})
res = {"model": a.model, "unit": unit, "asof": asof.date().isoformat(), "window_days": W,
       "normalization": {"received": len(raw), "normalized": len(norm), "duplicates_removed": dup, "rejected": rejected,
                         "unclassified": sorted({n["type"] for n in norm if not n["classified"]})}, "units": {}, "campaigns": {}, "hypotheses": [], "claims": []}
for u in units:
    N = [n for n in norm if n["unit"] == u]
    sc = lambda f: round(sum(n["weight"] for n in N if f(n["at"])), 2)
    c, p = sc(cur), sc(prev)
    chg = None if p == 0 else round((c - p) / abs(p) * 100, 1)
    ncur = sum(1 for n in N if cur(n["at"]))
    direction = "new engagement" if p == 0 and c > 0 else "no change" if c == p else "up" if c > p else "down"
    material = (p == 0 and ncur >= 3) or (chg is not None and abs(chg) >= 25 and ncur + sum(1 for n in N if prev(n["at"])) >= 3)
    ex = [n for n in N if n["executive"] and cur(n["at"])]; exp = [n for n in N if n["executive"] and prev(n["at"])]
    it = [n for n in N if n["category"] == "intent" and cur(n["at"])]; itp = [n for n in N if n["category"] == "intent" and prev(n["at"])]
    surge = len(it) >= 3 and len(it) >= 2 * max(len(itp), 1)
    topics = sorted({n["topic"] for n in N if n["topic"] and cur(n["at"])})
    neg = [n for n in N if n["category"] == "negative" and cur(n["at"])]
    res["units"][u] = {"engagement_score": {"current": c, "previous": p, "change_pct": chg, "direction": direction, "material": material, "signals_current": ncur},
        "executive_engagement": None if a.model == "B2C" else {"current": len(ex), "previous": len(exp), "roles": sorted({n["role"] for n in ex}), "evidence": [n["signal_id"] for n in ex]},
        "buying_intent": {"current": len(it), "previous": len(itp), "surge": surge, "types": sorted({n["type"] for n in it}), "evidence": [n["signal_id"] for n in it]},
        "topics": topics, "negative_signals": len(neg),
        "sources": sorted({n["source"] for n in N})}
    if material:
        res["claims"].append({"claim_type": "FACT", "text": f"{u}: engagement {direction} ({p} → {c} weighted points, {W}-day windows)", "evidence": [n["signal_id"] for n in N if cur(n["at"]) or prev(n["at"])][:20]})
# ---- 6–8 campaigns → accounts → opportunities (correlation unless experiment)
cmeta = {c["campaign_id"]: c for c in camps}
for cid in sorted({n["campaign_id"] for n in norm if n["campaign_id"]}):
    touches = [n for n in norm if n["campaign_id"] == cid]
    accts = sorted({n["unit"] for n in touches})
    infl = []
    for o in opps:
        if o.get("account_id") not in accts or not o.get("created_at"): continue
        oc = datetime.fromisoformat(str(o["created_at"])[:10])
        pre = [n for n in touches if n["unit"] == o["account_id"] and 0 <= (oc - n["at"]).days <= a.influence_days]
        if not pre: continue
        all_pre = [n for n in norm if n["unit"] == o["account_id"] and n["campaign_id"] and 0 <= (oc - n["at"]).days <= a.influence_days]
        share = round(len(pre) / len(all_pre), 3)
        exp = cmeta.get(cid, {}).get("experiment")
        infl.append({"opportunity_id": o["opportunity_id"], "account_id": o["account_id"], "touches_before_creation": len(pre),
                     "linear_touch_share": share, "influenced_amount": round(o.get("amount", 0) * share, 2) if o.get("amount") else None,
                     "claim_type": "CAUSAL_ESTIMATE" if exp and exp.get("holdout_lift") is not None else "CORRELATION",
                     "note": (f"holdout lift {exp['holdout_lift']} from {exp.get('source')}" if exp and exp.get("holdout_lift") is not None
                              else "touch preceded opportunity creation; influence is correlation, not proof of causation")})
    res["campaigns"][cid] = {"name": cmeta.get(cid, {}).get("name"), "accounts": accts, "touches": len(touches), "opportunities_influenced": infl}
# ---- 9 hypotheses: engagement + executive + relevant initiative (B2B); cohort growth (B2C); partner demand (B2B2C)
for u, v in res["units"].items():
    ev = v["buying_intent"]["evidence"] + (v["executive_engagement"]["evidence"] if v["executive_engagement"] else [])
    rel = [i for i in inits if i.get("account_id") == u and any(t_ in (i.get("topic") or "").lower() or (i.get("topic") or "").lower() in t_ for t_ in v["topics"])]
    if a.model == "B2B" and v["engagement_score"]["direction"] in ("up", "new engagement") and v["executive_engagement"]["current"] > 0:
        missing = [] if rel else ["a documented customer initiative matching the engaged topics"]
        if not v["buying_intent"]["current"]: missing.append("buying-intent signals")
        res["hypotheses"].append({"unit": u, "claim_type": "HYPOTHESIS", "type": "expansion",
            "text": f"{u} may be forming a buying initiative around {', '.join(v['topics']) or 'the engaged topics'}",
            "evidence": ev, "initiatives": [i.get("initiative_id") for i in rel], "missing_evidence": missing,
            "confidence": round(min(0.8, 0.3 + 0.15 * (v["executive_engagement"]["current"] > 0) + 0.15 * bool(rel) + 0.1 * v["buying_intent"]["surge"] + 0.05 * min(v["buying_intent"]["current"], 3)), 2)})
    if a.model == "B2C" and v["engagement_score"]["material"] and v["engagement_score"]["direction"] in ("up", "new engagement"):
        res["hypotheses"].append({"unit": u, "claim_type": "HYPOTHESIS", "type": "segment_demand", "text": f"Segment {u} shows rising demand; test offer/cohort expansion",
                                  "evidence": ev, "missing_evidence": ["conversion-rate change for the segment", "holdout test"], "confidence": 0.45})
    if a.model == "B2B2C" and v["buying_intent"]["current"] > 0:
        res["hypotheses"].append({"unit": u, "claim_type": "HYPOTHESIS", "type": "channel_demand", "text": f"Partner {u}: end-consumer demand signals rising; sell-in opportunity",
                                  "evidence": ev, "missing_evidence": ["partner sell-through data", "partner inventory"], "confidence": 0.4})
# ---- 10 persist
if a.memory_db:
    objs = []
    for n in norm:
        objs.append({"obj_id": n["signal_id"], "obj_type": "MarketingSignal", "account_id": n["unit"], "observed_at": n["at"].isoformat(), "source": n["source"],
                     "claim_type": "FACT", "confidence": 0.9 if n["classified"] else 0.5, "data": {k: n[k] for k in ["type", "category", "executive", "role", "campaign_id", "topic", "contact_id"]}})
    for u, v in res["units"].items():
        objs.append({"obj_type": "AccountEngagement", "account_id": u, "observed_at": res["asof"], "source": "marketing_signals.py", "claim_type": "FACT", "confidence": 0.85,
                     "data": {"engagement": v["engagement_score"], "executive": v["executive_engagement"], "intent": {k: v["buying_intent"][k] for k in ["current", "previous", "surge"]}}})
    for cid, c in res["campaigns"].items():
        for i in c["opportunities_influenced"]:
            objs.append({"obj_type": "CampaignInfluence", "account_id": i["account_id"], "opportunity_id": i["opportunity_id"], "observed_at": res["asof"],
                         "source": "marketing_signals.py", "claim_type": i["claim_type"], "confidence": 0.5, "data": dict(i, campaign_id=cid)})
    f = (a.out or "/tmp/ms") + ".objs.json"; json.dump(objs, open(f, "w"), default=str)
    mg = os.path.join(os.path.dirname(os.path.abspath(__file__)), "memory_graph.py")
    r = subprocess.run([sys.executable, mg, a.memory_db, "obj-put", f], capture_output=True, text=True)
    res["memory"] = json.loads(r.stdout) if r.stdout.startswith("{") else {"error": r.stdout or r.stderr}
# normalized per-signal list (V7.2 addition, backward compatible): categories assigned by THIS engine
res["normalized_signals"] = [{"signal_id": n["signal_id"], "unit": n["unit"], "type": n["type"], "category": n["category"], "executive": n["executive"],
                              "at": n["at"].isoformat(), "campaign_id": n["campaign_id"], "contact_id": n["contact_id"], "topic": n["topic"], "source": n["source"]} for n in norm]
print(json.dumps(res, indent=1, default=str))
if a.out: json.dump(res, open(a.out, "w"), indent=1, default=str)
