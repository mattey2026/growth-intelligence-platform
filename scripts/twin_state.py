#!/usr/bin/env python3
"""
twin_state.py (V7.1): Customer / Business Digital Twin with explicit state domains.

Domains: financial_state · marketing_state · competitive_state · competitive_threads · relationship_state ·
         commercial_state · market_state · operational_state
States:  HISTORICAL (all past snapshots) · CURRENT (latest snapshot) · FORECAST · WHAT_IF · TARGET
         (FORECAST / WHAT_IF / TARGET are stored separately and never mixed into CURRENT; TARGET requires --set-by)

USAGE
  twin_state.py DB snapshot ENTITY [--as-of DATE]     build the domains from memory objects, threads and facts; store as a snapshot
  twin_state.py DB view ENTITY                        CURRENT + latest FORECAST / WHAT_IF / TARGET + number of HISTORICAL snapshots
  twin_state.py DB changes ENTITY                     "what changed since the previous snapshot" (via domain_delta.py)
  twin_state.py DB export ENTITY --which current|previous --out snap.json
  twin_state.py DB set ENTITY --state forecast|whatif|target --domain D --metrics '{...}' --horizon DATE --source S [--assumptions "…"] [--set-by user]
"""
import sys, json, sqlite3, hashlib, os, subprocess, tempfile
from datetime import datetime
db, cmd, ent, *rest = sys.argv[1:]
def arg(k, d=None): return rest[rest.index(k) + 1] if k in rest else d
con = sqlite3.connect(db); con.row_factory = sqlite3.Row
con.execute("CREATE TABLE IF NOT EXISTS twin_snapshots(snapshot_id TEXT PRIMARY KEY, entity TEXT, as_of TEXT, created_at TEXT, domains TEXT)")
DOMAINS = ["financial_state", "marketing_state", "competitive_state", "competitive_threads", "relationship_state", "commercial_state", "market_state", "operational_state"]
def tbl(n): return con.execute("SELECT 1 FROM sqlite_master WHERE name=?", (n,)).fetchone() is not None
def objs(t):
    if not tbl("domain_objects"): return []
    return [dict(r) for r in con.execute("SELECT * FROM domain_objects WHERE account_id=? AND obj_type=? ORDER BY observed_at", (ent, t))]
def build():
    d = {k: {} for k in DOMAINS}
    for o in objs("FinancialMetric"):
        x = json.loads(o["data"]); d["financial_state"][x["metric"]] = {"value": x["value"], "period": x.get("period"), "source": o["source"], "as_of": o["observed_at"], "confidence": o["confidence"]}
    for o in objs("FinancialSignal"):
        x = json.loads(o["data"]); d["financial_state"]["signal:" + x["kind"]] = {"value": x["text"], "source": o["source"], "as_of": o["observed_at"]}
    for o in objs("AccountEngagement"):
        x = json.loads(o["data"]); d["marketing_state"] = {"engagement_current": {"value": x["engagement"]["current"], "source": o["source"], "as_of": o["observed_at"]},
            "engagement_direction": {"value": x["engagement"]["direction"], "source": o["source"], "as_of": o["observed_at"]},
            "executive_engagement": {"value": (x.get("executive") or {}).get("current"), "source": o["source"], "as_of": o["observed_at"]},
            "intent_surge": {"value": x["intent"]["surge"], "source": o["source"], "as_of": o["observed_at"]}}
    for o in objs("CampaignInfluence"):
        x = json.loads(o["data"]); d["marketing_state"][f"influence:{x['campaign_id']}:{o['opportunity_id']}"] = {"value": x["linear_touch_share"], "source": o["source"], "as_of": o["observed_at"], "claim_type": o["claim_type"]}
    for o in objs("CompetitiveEvent"):
        x = json.loads(o["data"]); d["competitive_state"][f"{o['competitor_id']}:presence"] = {"value": "active", "source": o["source"], "as_of": o["observed_at"]}
    if tbl("competitive_threads"):
        for r in con.execute("SELECT * FROM competitive_threads WHERE account_id=?", (ent,)):
            d["competitive_threads"][r["thread_id"]] = {"value": {"status": r["status"], "momentum": r["momentum"], "risk": r["risk_level"], "signals": r["signal_count"], "confidence": r["confidence"]},
                                                        "source": "competitive_threads", "as_of": r["latest_signal"]}
    for o in objs("CrossDomainPattern"):
        x = json.loads(o["data"]); d["commercial_state"]["pattern:" + x["pattern_id"]] = {"value": x["status"], "source": o["source"], "as_of": o["observed_at"]}
    if tbl("facts"):
        for r in con.execute("SELECT attribute,value,source,observed_at FROM facts WHERE entity=? AND is_current=1", (ent,)):
            dom = ("relationship_state" if r["attribute"].startswith(("rel_", "champion", "sponsor")) else "operational_state" if r["attribute"] in ("open_cases", "open_sev12_cases", "payment_status")
                   or r["attribute"].startswith("adoption_") else "commercial_state" if r["attribute"] in ("open_pipeline", "revenue", "days_to_renewal", "renewal_risk", "health") else "market_state" if r["attribute"].startswith("market_") else None)
            if dom: d[dom][r["attribute"]] = {"value": r["value"], "source": r["source"], "as_of": r["observed_at"]}
    return d
snaps = lambda: [dict(r) for r in con.execute("SELECT * FROM twin_snapshots WHERE entity=? ORDER BY created_at, rowid", (ent,))]
if cmd == "snapshot":
    d = build(); asof = arg("--as-of", datetime.now().date().isoformat())
    sid = "TWS-" + hashlib.sha1(f"{ent}{asof}{datetime.now()}".encode()).hexdigest()[:8]
    con.execute("INSERT INTO twin_snapshots VALUES(?,?,?,?,?)", (sid, ent, asof, datetime.now().isoformat(timespec="seconds"), json.dumps(d, default=str))); con.commit()
    print(json.dumps({"snapshot_id": sid, "entity": ent, "as_of": asof, "domain_sizes": {k: len(v) for k, v in d.items()},
                      "empty_domains": [k for k, v in d.items() if not v]}))
elif cmd in ("export", "changes"):
    S = snaps()
    def snap(i): return {"account_id": ent, "as_of": S[i]["as_of"], "domains": json.loads(S[i]["domains"])}
    if cmd == "export":
        i = -1 if arg("--which", "current") == "current" else -2
        if len(S) < abs(i): print(json.dumps({"error": "not enough snapshots"})); sys.exit(1)
        json.dump(snap(i), open(arg("--out"), "w"), default=str); print(json.dumps({"exported": arg("--out"), "as_of": S[i]["as_of"]}))
    else:
        if len(S) < 2: print(json.dumps({"error": "need two snapshots; only " + str(len(S))})); sys.exit(1)
        d = tempfile.mkdtemp(); json.dump(snap(-2), open(f"{d}/p.json", "w"), default=str); json.dump(snap(-1), open(f"{d}/n.json", "w"), default=str)
        r = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "domain_delta.py"), f"{d}/p.json", f"{d}/n.json"], capture_output=True, text=True)
        print(r.stdout)
elif cmd == "view":
    S = snaps(); cur = json.loads(S[-1]["domains"]) if S else {}
    st = {}
    for r in con.execute("SELECT data,created_at,status FROM ledger WHERE kind='scenario' AND entity=? AND status IN ('forecast','whatif','target') ORDER BY created_at", (ent,)) if tbl("ledger") else []:
        st.setdefault(r["status"], []).append(dict(json.loads(r["data"]), at=r["created_at"]))
    print(json.dumps({"entity": ent, "HISTORICAL": [{"snapshot_id": s["snapshot_id"], "as_of": s["as_of"]} for s in S[:-1]],
                      "CURRENT": {"as_of": S[-1]["as_of"] if S else None, "domains": cur}, "FORECAST": st.get("forecast", [])[-1:],
                      "WHAT_IF": st.get("whatif", [])[-3:], "TARGET": st.get("target", [])[-1:],
                      "note": "FORECAST and WHAT_IF are predictions or scenarios, not facts; TARGET is a decision."}, indent=1, default=str))
elif cmd == "set":
    stt = arg("--state")
    if stt == "target" and not arg("--set-by"): print(json.dumps({"refused": "TARGET requires --set-by (a user or an approved plan)"})); sys.exit(1)
    if arg("--domain") and arg("--domain") not in DOMAINS: print(json.dumps({"refused": f"domain must be one of {DOMAINS}"})); sys.exit(1)
    con.execute("CREATE TABLE IF NOT EXISTS ledger(id TEXT PRIMARY KEY, kind TEXT, entity TEXT, text TEXT, data TEXT, created_at TEXT, run_id TEXT, status TEXT, links TEXT, next_review TEXT, confidence REAL)")
    sid = "STA-" + hashlib.sha1(f"{ent}{stt}{datetime.now()}".encode()).hexdigest()[:8]
    con.execute("INSERT INTO ledger(id,kind,entity,text,data,created_at,status) VALUES(?,?,?,?,?,?,?)", (sid, "scenario", ent, f"{stt} {arg('--domain')} to {arg('--horizon')}",
                json.dumps({"state": stt, "domain": arg("--domain"), "metrics": json.loads(arg("--metrics")), "horizon": arg("--horizon"), "source": arg("--source"),
                            "assumptions": arg("--assumptions"), "set_by": arg("--set-by")}), datetime.now().isoformat(timespec="seconds"), stt))
    con.commit(); print(json.dumps({"state_id": sid, "state": stt}))
