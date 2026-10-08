#!/usr/bin/env python3
"""
competitive_threads.py: persistent CompetitiveThread engine (V7.1).

A CompetitiveThread is a first-class, persistent object in Business Memory (tables `competitive_threads` and
`thread_signals` in the same SQLite memory file, tenant-scoped). Signals about the same account + competitor +
thread family are associated with ONE thread instead of becoming independent observations.

Signal kinds (polarity: +1 strengthens the competitor's position, -1 weakens it / counter-evidence):
  +1 rfp_participation, competitor_shortlisted, pricing_undercut, competitor_exec_meeting, competitor_pilot,
     competitor_hire_into_account, champion_weakening, competitor_reference, competitor_contract_award
  -1 competitor_delivery_issue, competitor_exit, our_win_against, customer_positive_on_us, competitor_price_rise
Thread families: displacement_risk (they threaten our position), displacement_opportunity (we can displace them),
  competitive_pursuit (a contested new deal).

USAGE (DB = memory file)
  competitive_threads.py DB ingest signals.json [--window-days 180] [--asof DATE]   match-or-create per signal
  competitive_threads.py DB get THREAD_ID
  competitive_threads.py DB query [--account A] [--competitor C] [--opportunity O] [--status S] [--since D]
  competitive_threads.py DB link THREAD_ID [--opportunity O] [--stakeholder C] [--campaign M] [--financial-signal F]
                         [--relationship-signal R] [--market-signal S]
  competitive_threads.py DB outcome THREAD_ID --outcome won|lost|competitor_exited|no_decision --date D [--evidence "…"]
  competitive_threads.py DB snapshot [--account A]          thread states for delta comparison
"""
import sys, json, sqlite3, hashlib, argparse, os
from datetime import datetime, timedelta
POS = {"rfp_participation": 3, "competitor_shortlisted": 3, "pricing_undercut": 2, "competitor_exec_meeting": 2, "competitor_pilot": 3,
       "competitor_hire_into_account": 2, "champion_weakening": 2, "competitor_reference": 1, "competitor_contract_award": 4, "competitor_mention": 1}
NEG = {"competitor_delivery_issue": 2, "competitor_exit": 4, "our_win_against": 3, "customer_positive_on_us": 1, "competitor_price_rise": 1}
FAMILY = {"competitor_delivery_issue": "displacement_opportunity", "competitor_exit": "displacement_opportunity", "competitor_price_rise": "displacement_opportunity"}
NEXT = {"rfp_participation": "Competitor shortlisted or submits pricing within 30–60 days", "competitor_shortlisted": "Commercial negotiation / BAFO within 30 days",
        "pricing_undercut": "Pressure for a price concession on renewal or active deal", "competitor_exec_meeting": "Competitor proposal or pilot offer within 60 days",
        "competitor_pilot": "Pilot-to-production decision within 90 days", "champion_weakening": "Loss of internal sponsorship; decision reopened",
        "competitor_hire_into_account": "Competitor gains insider access; RFP or re-bid likely within 6 months",
        "competitor_contract_award": "Scope transfer / transition planning", "competitor_delivery_issue": "Customer opens alternatives (RFI) within 90 days",
        "competitor_exit": "Transition of scope; replacement vendor selection"}
SCHEMA = """CREATE TABLE IF NOT EXISTS competitive_threads(thread_id TEXT PRIMARY KEY, tenant TEXT, account_id TEXT, competitor_id TEXT, thread_type TEXT,
  status TEXT, title TEXT, description TEXT, created_at TEXT, updated_at TEXT, first_signal TEXT, latest_signal TEXT, signal_count INTEGER,
  signal_velocity REAL, confidence REAL, risk_level TEXT, opportunity_level TEXT, stakeholders TEXT, opportunities TEXT, campaigns TEXT,
  financial_signals TEXT, relationship_signals TEXT, market_signals TEXT, evidence TEXT, source_history TEXT, chronology TEXT, hypotheses TEXT,
  counter_evidence TEXT, predicted_next_event TEXT, recommended_actions TEXT, owner TEXT, outcome TEXT, outcome_date TEXT, momentum TEXT);
CREATE TABLE IF NOT EXISTS thread_signals(signal_id TEXT PRIMARY KEY, thread_id TEXT, observed_at TEXT, kind TEXT, polarity INTEGER, strength REAL,
  source TEXT, text TEXT, links TEXT);"""
LISTS = ["stakeholders", "opportunities", "campaigns", "financial_signals", "relationship_signals", "market_signals", "evidence", "source_history",
         "chronology", "hypotheses", "counter_evidence", "recommended_actions"]
db, cmd, *rest = sys.argv[1:]
con = sqlite3.connect(db); con.row_factory = sqlite3.Row; con.executescript(SCHEMA)
con.execute("CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT)")
_b = con.execute("SELECT value FROM meta WHERE key='tenant'").fetchone(); _t = os.environ.get("GROWTH_TENANT")
if _b and _t and _b[0] != _t:
    print(json.dumps({"error": f"tenant isolation: memory belongs to '{_b[0]}'"})); sys.exit(3)
TEN = _t or (_b[0] if _b else "default")
D = lambda s: datetime.fromisoformat(str(s)[:10])

def load(tid):
    r = con.execute("SELECT * FROM competitive_threads WHERE thread_id=? AND tenant=?", (tid, TEN)).fetchone()
    if not r: return None
    t = dict(r)
    for k in LISTS: t[k] = json.loads(t[k] or "[]")
    if t.get("predicted_next_event") and str(t["predicted_next_event"]).startswith("{"): t["predicted_next_event"] = json.loads(t["predicted_next_event"])
    t["signals"] = [dict(x) for x in con.execute("SELECT * FROM thread_signals WHERE thread_id=? ORDER BY observed_at", (tid,))]
    return t

def save(t):
    row = {k: (json.dumps(v, default=str) if (k in LISTS or isinstance(v, (dict, list))) else v) for k, v in t.items() if k != "signals"}
    cols = ",".join(row); con.execute(f"INSERT OR REPLACE INTO competitive_threads({cols}) VALUES({','.join('?' * len(row))})", list(row.values()))

def recompute(t, asof):
    S = t["signals"]
    # For THREAT threads the supporting signals are the competitor gaining ground (polarity +1) and counter-evidence is −1.
    # For a displacement OPPORTUNITY the competitor's weakness (−1) is the support and its gains (+1) are counter-evidence.
    opp = t["thread_type"] == "displacement_opportunity"
    pos = [s for s in S if (s["polarity"] < 0 if opp else s["polarity"] > 0)]      # supporting the thread's hypothesis
    neg = [s for s in S if (s["polarity"] > 0 if opp else s["polarity"] < 0)]      # counter-evidence
    t["signal_count"] = len(S); t["first_signal"] = S[0]["observed_at"]; t["latest_signal"] = S[-1]["observed_at"]
    w = lambda a, b: [s for s in S if a < (asof - D(s["observed_at"])).days <= b]
    wpos = lambda a_, b_: [s for s in w(a_, b_) if s in pos]
    rec, prior = len(wpos(-1, 60)), len(wpos(60, 120))       # momentum is measured on SUPPORTING signals only
    t["signal_velocity"] = round(len(w(-1, 90)) / 3.0, 2)                  # signals per 30 days over the last 90 days
    rec_pos, rec_neg = len([s for s in w(-1, 60) if s in pos]), len([s for s in w(-1, 60) if s in neg])
    stale = (asof - D(t["latest_signal"])).days > 90
    if t.get("outcome"): t["momentum"] = "resolved"
    elif stale: t["momentum"] = "weakening (no signals in 90+ days)"
    elif rec_neg > 0 and rec_neg >= rec_pos: t["momentum"] = "weakening (recent counter-evidence matches or exceeds support)"
    elif rec >= 2 and rec >= 1.5 * max(prior, 1): t["momentum"] = "accelerating"
    elif prior > 0 and rec <= 0.5 * prior: t["momentum"] = "weakening"
    else: t["momentum"] = "steady"
    t["counter_evidence"] = [{"at": s["observed_at"], "kind": s["kind"], "text": s["text"], "source": s["source"]} for s in neg]
    srcs = {s["source"] for s in S}
    psrcs = {s["source"] for s in pos}                        # only supporting sources strengthen the threat hypothesis
    conf = 0.30 + 0.08 * min(len(psrcs), 4) + 0.05 * min(len(pos), 6) - (0.2 * len(neg) / len(S) if S else 0)
    t["confidence"] = round(max(0.1, min(0.9, conf)), 2)
    score = sum(s["strength"] for s in pos) - sum(s["strength"] for s in neg)       # net support for the thread's hypothesis
    if opp:
        t["opportunity_level"] = "High" if score >= 5 or any(s["kind"] == "competitor_exit" for s in pos) else "Medium" if score > 0 else "Low"
        t["risk_level"] = "Low"
    else:
        t["risk_level"] = "High" if score >= 7 or (score >= 5 and t["momentum"] == "accelerating") else "Medium" if score >= 3 else "Low"
        t["opportunity_level"] = "Low"
    last = S[-1]["kind"]
    t["predicted_next_event"] = None if t.get("outcome") else {"event": NEXT.get(last, "Further competitor engagement"), "basis": f"rule: last signal '{last}'",
                                                               "claim_type": "PREDICTION", "confidence": "Low" if len(S) < 3 else "Medium"}
    t["status"] = "resolved" if t.get("outcome") else ("active" if not stale else "dormant")
    acts = []
    if t["thread_type"] != "displacement_opportunity" and t["risk_level"] in ("High", "Medium"):
        acts.append({"action": "Executive sponsor call to re-confirm the value case", "why": f"risk {t['risk_level']}, momentum {t['momentum']}"})
        if any(s["kind"] == "champion_weakening" for s in S): acts.append({"action": "Re-thread: build a second champion", "why": "champion weakening"})
        if any(s["kind"] == "pricing_undercut" for s in S): acts.append({"action": "Prepare value-based response; no unapproved price concession", "why": "competitor pricing pressure"})
    if t["thread_type"] == "displacement_opportunity": acts.append({"action": "Qualify a displacement pursuit with the sponsor", "why": "competitor weakening"})
    t["recommended_actions"] = [dict(a, claim_type="RECOMMENDATION", approval_required=True) for a in acts]
    gaining = (score > 0) != opp
    t["hypotheses"] = [{"text": f"{t['competitor_id']} is {'gaining' if gaining else 'losing'} ground at {t['account_id']}", "claim_type": "HYPOTHESIS",
                        "support": len(pos), "against": len(neg)}]
    t["chronology"] = [{"at": s["observed_at"], "kind": s["kind"], "polarity": s["polarity"], "text": s["text"]} for s in S]
    t["source_history"] = sorted(srcs); t["evidence"] = [{"signal_id": s["signal_id"], "source": s["source"], "at": s["observed_at"]} for s in S]
    t["updated_at"] = datetime.now().isoformat(timespec="seconds")
    return t

def memobj(o):
    con.execute("CREATE TABLE IF NOT EXISTS domain_objects(obj_id TEXT PRIMARY KEY, obj_type TEXT, tenant TEXT, account_id TEXT, competitor_id TEXT, opportunity_id TEXT, observed_at TEXT, recorded_at TEXT, source TEXT, source_date TEXT, confidence REAL, claim_type TEXT, data TEXT)")
    con.execute("INSERT OR REPLACE INTO domain_objects VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)", (o["obj_id"], o["obj_type"], TEN, o["account_id"], o.get("competitor_id"),
                o.get("opportunity_id"), o["observed_at"], datetime.now().isoformat(timespec="seconds"), o["source"], o.get("source_date"), o.get("confidence"),
                o.get("claim_type"), json.dumps(o.get("data", {}), default=str)))

ap = argparse.ArgumentParser(); ap.add_argument("x", nargs="*"); ap.add_argument("--window-days", type=int, default=180); ap.add_argument("--asof")
for k in ["account", "competitor", "opportunity", "status", "since", "stakeholder", "campaign", "financial-signal", "relationship-signal", "market-signal", "outcome", "date", "evidence"]:
    ap.add_argument("--" + k)
a = ap.parse_args(rest)
asof = D(a.asof) if a.asof else datetime.now()

if cmd == "ingest":
    sigs = json.load(open(a.x[0])); res = []
    for s in sorted(sigs, key=lambda z: z["observed_at"]):
        kind = s["kind"]; pol = 1 if kind in POS else -1 if kind in NEG else 0
        if pol == 0:
            res.append({"signal": s.get("signal_id"), "action": "REJECTED", "reason": f"unknown kind '{kind}'"}); continue
        if not s.get("source") or not s.get("account_id") or not s.get("competitor_id"):
            res.append({"signal": s.get("signal_id"), "action": "REJECTED", "reason": "account_id, competitor_id and source are required"}); continue
        fam = s.get("thread_type") or FAMILY.get(kind) or ("competitive_pursuit" if s.get("opportunity_id") and kind in ("rfp_participation", "competitor_shortlisted") else "displacement_risk")
        sid = s.get("signal_id") or "CS-" + hashlib.sha1(json.dumps(s, sort_keys=True).encode()).hexdigest()[:10]
        if con.execute("SELECT 1 FROM thread_signals WHERE signal_id=?", (sid,)).fetchone():
            res.append({"signal": sid, "action": "DUPLICATE_IGNORED"}); continue
        # MATCH: same tenant + account + competitor; same family (a displacement_opportunity signal may attach to an
        # open displacement_risk thread as counter-evidence); active within the window.
        cands = [dict(r) for r in con.execute("SELECT thread_id, thread_type, latest_signal, status FROM competitive_threads WHERE tenant=? AND account_id=? AND competitor_id=? AND status!='resolved'",
                                              (TEN, s["account_id"], s["competitor_id"]))]
        # Families: THREAT = {displacement_risk, competitive_pursuit} (the competitor gaining ground here) and
        # OPPORTUNITY = {displacement_opportunity}. Signals match any open thread in the same family; counter-evidence
        # (polarity −1) attaches to an open THREAT thread before it may start an OPPORTUNITY thread.
        THREAT = {"displacement_risk", "competitive_pursuit"}
        def compatible(ctype):
            if fam in THREAT: return ctype in THREAT
            if pol < 0: return ctype in THREAT or ctype == fam
            return ctype == fam
        cands = [c for c in cands if (D(s["observed_at"]) - D(c["latest_signal"])).days <= a.window_days and compatible(c["thread_type"])]
        cands.sort(key=lambda c: (c["thread_type"] not in THREAT if pol < 0 else 0, c["latest_signal"]), reverse=False)
        if cands:
            t = load(cands[0]["thread_id"]); action = "UPDATED"
            if fam == "competitive_pursuit" and t["thread_type"] == "displacement_risk": t["thread_type"] = "competitive_pursuit"   # an RFP makes it a contested pursuit
        else:
            tid = "CT-" + hashlib.sha1(f"{TEN}{s['account_id']}{s['competitor_id']}{fam}{s['observed_at']}".encode()).hexdigest()[:8]
            t = {"thread_id": tid, "tenant": TEN, "account_id": s["account_id"], "competitor_id": s["competitor_id"], "thread_type": fam, "status": "new",
                 "title": f"{s['competitor_id']} — {fam.replace('_', ' ')} at {s['account_id']}", "description": s.get("text", ""),
                 "created_at": datetime.now().isoformat(timespec="seconds"), "owner": s.get("owner"), "outcome": None, "outcome_date": None, "signals": []}
            for k in LISTS: t[k] = []
            action = "CREATED"
        links = {k: s[k] for k in ["opportunity_id", "stakeholder_id", "campaign_id", "financial_signal", "relationship_signal", "market_signal"] if s.get(k)}
        con.execute("INSERT INTO thread_signals VALUES(?,?,?,?,?,?,?,?,?)", (sid, t["thread_id"], str(s["observed_at"])[:10], kind, pol,
                    float(s.get("strength", POS.get(kind) or NEG.get(kind))), s["source"], s.get("text", ""), json.dumps(links)))
        t["signals"].append({"signal_id": sid, "observed_at": str(s["observed_at"])[:10], "kind": kind, "polarity": pol,
                             "strength": float(s.get("strength", POS.get(kind) or NEG.get(kind))), "source": s["source"], "text": s.get("text", ""), "links": json.dumps(links)})
        for lk, col in [("opportunity_id", "opportunities"), ("stakeholder_id", "stakeholders"), ("campaign_id", "campaigns"), ("financial_signal", "financial_signals"),
                        ("relationship_signal", "relationship_signals"), ("market_signal", "market_signals")]:
            if s.get(lk) and s[lk] not in t[col]: t[col].append(s[lk])
        before = (t.get("confidence"), t.get("momentum"))
        t = recompute(t, asof if a.asof else D(s["observed_at"]))
        save(t)
        memobj({"obj_id": "CEV-" + sid, "obj_type": "CompetitiveEvent", "account_id": s["account_id"], "competitor_id": s["competitor_id"], "opportunity_id": s.get("opportunity_id"),
                "observed_at": str(s["observed_at"])[:10], "source": s["source"], "confidence": s.get("confidence", 0.8 if s.get("verified", True) else 0.5), "claim_type": "FACT" if s.get("verified", True) else "INFERENCE",
                "data": {"kind": kind, "polarity": pol, "text": s.get("text"), "thread_id": t["thread_id"]}})
        res.append({"signal": sid, "action": action, "thread_id": t["thread_id"], "signal_count": t["signal_count"], "confidence_before": before[0],
                    "confidence_after": t["confidence"], "momentum": t["momentum"], "risk": t["risk_level"]})
    for tid in {r["thread_id"] for r in res if r.get("thread_id")}:
        t = load(tid)
        memobj({"obj_id": "CTH-" + tid, "obj_type": "CompetitiveThread", "account_id": t["account_id"], "competitor_id": t["competitor_id"],
                "opportunity_id": (t["opportunities"] or [None])[0], "observed_at": t["latest_signal"], "source": "competitive_threads.py", "confidence": t["confidence"],
                "claim_type": "INFERENCE", "data": {"thread_id": tid, "status": t["status"], "momentum": t["momentum"], "risk": t["risk_level"], "signals": t["signal_count"]}})
        for i, h in enumerate(t["hypotheses"]):
            memobj({"obj_id": f"CHY-{tid}-{i}", "obj_type": "CompetitiveHypothesis", "account_id": t["account_id"], "competitor_id": t["competitor_id"],
                    "observed_at": t["latest_signal"], "source": "competitive_threads.py", "confidence": t["confidence"], "claim_type": "HYPOTHESIS", "data": h})
    con.commit(); print(json.dumps(res, indent=1))
elif cmd == "get":
    t = load(a.x[0]); print(json.dumps(t, indent=1, default=str) if t else json.dumps({"error": "not found"}))
elif cmd == "query":
    w, p = ["tenant=?"], [TEN]
    for col, v in [("account_id", a.account), ("competitor_id", a.competitor), ("status", a.status)]:
        if v: w.append(f"{col}=?"); p.append(v)
    if a.since: w.append("latest_signal>=?"); p.append(a.since)
    rows = [dict(r) for r in con.execute(f"SELECT * FROM competitive_threads WHERE {' AND '.join(w)} ORDER BY latest_signal DESC", p)]
    if a.opportunity: rows = [r for r in rows if a.opportunity in json.loads(r["opportunities"] or "[]")]
    for r in rows:
        for k in LISTS: r[k] = json.loads(r[k] or "[]")
        if r.get("predicted_next_event") and str(r["predicted_next_event"]).startswith("{"): r["predicted_next_event"] = json.loads(r["predicted_next_event"])
    print(json.dumps(rows, indent=1, default=str))
elif cmd == "link":
    t = load(a.x[0])
    for arg_, col in [("opportunity", "opportunities"), ("stakeholder", "stakeholders"), ("campaign", "campaigns"), ("financial_signal", "financial_signals"),
                      ("relationship_signal", "relationship_signals"), ("market_signal", "market_signals")]:
        v = getattr(a, arg_)
        if v and v not in t[col]: t[col].append(v)
    save(t); con.commit(); print(json.dumps({k: t[k] for k in ["thread_id", "opportunities", "stakeholders", "campaigns", "financial_signals", "relationship_signals", "market_signals"]}))
elif cmd == "outcome":
    t = load(a.x[0]); assert a.outcome in ("won", "lost", "competitor_exited", "no_decision")
    pred = t.get("predicted_next_event"); t["outcome"], t["outcome_date"] = a.outcome, a.date
    t = recompute(t, D(a.date)); save(t)
    memobj({"obj_id": "COU-" + t["thread_id"], "obj_type": "CompetitiveOutcome", "account_id": t["account_id"], "competitor_id": t["competitor_id"],
            "observed_at": a.date, "source": a.evidence or "user-recorded outcome", "claim_type": "FACT",
            "data": {"thread_id": t["thread_id"], "outcome": a.outcome, "prediction_at_close": pred, "risk_at_close": t["risk_level"]}})
    con.commit(); print(json.dumps({"thread_id": t["thread_id"], "status": t["status"], "outcome": a.outcome, "prediction_was": pred}))
elif cmd == "snapshot":
    w, p = ["tenant=?"], [TEN]
    if a.account: w.append("account_id=?"); p.append(a.account)
    rows = [dict(r) for r in con.execute(f"SELECT thread_id,status,momentum,risk_level,opportunity_level,signal_count,confidence,latest_signal FROM competitive_threads WHERE {' AND '.join(w)}", p)]
    print(json.dumps({r["thread_id"]: r for r in rows}, indent=1))
