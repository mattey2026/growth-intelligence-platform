#!/usr/bin/env python3
"""
learning_manager.py: Outcome & Learning Manager (controlled, never self-modifying).

Lifecycle: candidate → validated | rejected → adopted (versioned rule) → retired
  candidate  created from outcomes (prediction error, action variance, win/loss pattern)
  validate   needs evidence: ≥ N comparable outcomes (default 20) with a consistent error sign, OR a passing
             backtest artifact; otherwise it stays a candidate
  adopt      requires an explicit approver (model owner); writes a versioned rule to the `rules` table
Skills read adopted rules (rules --active) before scoring. Nothing changes prompts, code, or models automatically.
USAGE: learning_manager.py DB candidate --scope "segment=…" --rule "…" --evidence-ids OUT-1,OUT-2 | evaluate CAND_ID [--min-n 20] [--backtest file.json]
       | adopt CAND_ID --by model_owner | retire RULE_ID --by … | rules [--active]
"""
import sys, json, sqlite3, hashlib
from datetime import datetime
db, cmd, *rest = sys.argv[1:]
def arg(k, d=None): return rest[rest.index(k) + 1] if k in rest else d
con = sqlite3.connect(db); con.row_factory = sqlite3.Row; now = datetime.now().isoformat(timespec="seconds")
con.execute("CREATE TABLE IF NOT EXISTS rules(rule_id TEXT PRIMARY KEY, version INTEGER, scope TEXT, rule TEXT, source_candidate TEXT, adopted_by TEXT, adopted_at TEXT, status TEXT)")
if cmd == "candidate":
    cid = "LCA-" + hashlib.sha1((arg("--rule") + now).encode()).hexdigest()[:8]
    ev = [e for e in (arg("--evidence-ids") or "").split(",") if e]
    con.execute("INSERT INTO ledger(id,kind,entity,text,data,created_at,status) VALUES(?,?,?,?,?,?,?)",
                (cid, "learning", arg("--scope", "portfolio"), arg("--rule"), json.dumps({"evidence_ids": ev, "stage": "candidate"}), now, "candidate"))
    con.commit(); print(json.dumps({"candidate": cid, "evidence_items": len(ev), "stage": "candidate"}))
elif cmd == "evaluate":
    cid = rest[0]; r = con.execute("SELECT * FROM ledger WHERE id=?", (cid,)).fetchone(); d = json.loads(r["data"])
    outs = [json.loads(x[0]) for x in con.execute(f"SELECT data FROM ledger WHERE kind='outcome' AND id IN ({','.join('?' * len(d['evidence_ids']))})", d["evidence_ids"])] if d["evidence_ids"] else []
    errs = [o.get("error") for o in outs if o.get("error") is not None]
    minn = int(arg("--min-n", 20)); bt = json.load(open(arg("--backtest"))) if arg("--backtest") else None
    consistent = errs and (all(e > 0 for e in errs) or all(e < 0 for e in errs))
    ok = (len(errs) >= minn and consistent) or (bt and bt.get("improved") is True)
    stage = "validated" if ok else "candidate"
    reason = (f"{len(errs)} outcomes (need ≥{minn})" + ("; consistent error sign" if consistent else "; inconsistent or no errors")) + (f"; backtest improved={bt.get('improved')}" if bt else "")
    d.update(stage=stage, validation=reason); con.execute("UPDATE ledger SET status=?, data=? WHERE id=?", (stage, json.dumps(d), cid)); con.commit()
    print(json.dumps({"candidate": cid, "stage": stage, "reason": reason}))
elif cmd == "adopt":
    cid = rest[0]; r = con.execute("SELECT * FROM ledger WHERE id=?", (cid,)).fetchone()
    if r["status"] != "validated": print(json.dumps({"refused": f"candidate is '{r['status']}', not validated. Learning is never adopted without validation"})); sys.exit(1)
    if not arg("--by"): print(json.dumps({"refused": "an approver (model owner) is required"})); sys.exit(1)
    ver = 1 + (con.execute("SELECT MAX(version) FROM rules WHERE scope=?", (r["entity"],)).fetchone()[0] or 0)
    rid = f"RULE-{r['entity']}-v{ver}".replace(" ", "_")
    con.execute("UPDATE rules SET status='superseded' WHERE scope=? AND status='active'", (r["entity"],))
    con.execute("INSERT INTO rules VALUES(?,?,?,?,?,?,?,?)", (rid, ver, r["entity"], r["text"], cid, arg("--by"), now, "active"))
    con.execute("UPDATE ledger SET status='adopted' WHERE id=?", (cid,)); con.commit()
    print(json.dumps({"rule": rid, "version": ver, "status": "active", "adopted_by": arg("--by")}))
elif cmd == "retire":
    con.execute("UPDATE rules SET status='retired' WHERE rule_id=?", (rest[0],)); con.commit(); print(json.dumps({"retired": rest[0]}))
elif cmd == "rules":
    q = "SELECT * FROM rules" + (" WHERE status='active'" if "--active" in rest else "")
    print(json.dumps([dict(x) for x in con.execute(q)], indent=1))
