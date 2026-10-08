#!/usr/bin/env python3
"""
action_manager.py: Action Manager (Recommendation → Risk/Policy/Approval → Action → Result → Outcome → Memory).

Keeps an auditable lifecycle for every action in the Memory Graph ledger (kind=action), with states:
  proposed → gated(ALLOW|REQUIRE_APPROVAL|DENY) → approved|rejected → executed|failed → outcome_linked
It does NOT call external systems itself: execution happens through the user's authorized connector in the
main session, and the result is recorded here. A step cannot be skipped.
USAGE
  action_manager.py DB propose  --action email.send --entity A002 --spec spec.json --from-rec REC-id --agent deal-strategy-agent
  action_manager.py DB gate     ACT-id --decision REQUIRE_APPROVAL --approver user --reasons "…"
  action_manager.py DB approve  ACT-id --by u1        |  reject ACT-id --by u1 --why "…"
  action_manager.py DB executed ACT-id --result '{"system":"CRM","record":"T-991","status":"created"}'  |  failed ACT-id --error "…"
  action_manager.py DB outcome  ACT-id --expected "…" --actual "…" [--variance "…"]
  action_manager.py DB audit    [ACT-id]
"""
import sys, json, sqlite3, hashlib
from datetime import datetime
db, cmd, *rest = sys.argv[1:]
con = sqlite3.connect(db); con.row_factory = sqlite3.Row
con.execute("CREATE TABLE IF NOT EXISTS action_log(action_id TEXT, at TEXT, state TEXT, by TEXT, detail TEXT)")
now = lambda: datetime.now().isoformat(timespec="seconds")
def arg(k, d=None):
    return rest[rest.index(k) + 1] if k in rest else d
ORDER = {"proposed": 0, "gated": 1, "approved": 2, "rejected": 2, "executed": 3, "failed": 3, "outcome_linked": 4}
def state(aid):
    r = con.execute("SELECT state FROM action_log WHERE action_id=? ORDER BY rowid DESC LIMIT 1", (aid,)).fetchone()
    return r[0] if r else None
def log(aid, st, by, detail):
    con.execute("INSERT INTO action_log VALUES(?,?,?,?,?)", (aid, now(), st, by, json.dumps(detail))); con.commit()
def need(aid, allowed):
    s = state(aid)
    if s not in allowed:
        print(json.dumps({"error": f"illegal transition from {s} (allowed from {allowed})", "action": aid})); sys.exit(1)
    return s
if cmd == "propose":
    act, ent = arg("--action"), arg("--entity")
    aid = "ACT-" + hashlib.sha1(f"{act}{ent}{now()}".encode()).hexdigest()[:8]
    spec = json.load(open(arg("--spec"))) if arg("--spec") else {}
    con.execute("INSERT INTO ledger(id,kind,entity,text,data,created_at,status,links) VALUES(?,?,?,?,?,?,?,?)",
                (aid, "action", ent, f"{act} proposed", json.dumps({"action": act, "spec": spec, "agent": arg("--agent")}), now(), "proposed", arg("--from-rec")))
    log(aid, "proposed", arg("--agent", "orchestrator"), {"action": act, "spec": spec, "from_recommendation": arg("--from-rec")})
    print(json.dumps({"action_id": aid, "state": "proposed"}))
elif cmd == "gate":
    aid = rest[0]; need(aid, ["proposed"]); d = arg("--decision")
    log(aid, "gated", "policy_gate", {"decision": d, "approver": arg("--approver"), "reasons": arg("--reasons")})
    if d == "DENY":
        log(aid, "rejected", "policy_gate", {"why": arg("--reasons")})
    elif d == "ALLOW":
        log(aid, "approved", "policy (no per-item approval required)", {})
    print(json.dumps({"action_id": aid, "gate": d, "state": state(aid)}))
elif cmd in ("approve", "reject"):
    aid = rest[0]; need(aid, ["gated"])
    log(aid, "approved" if cmd == "approve" else "rejected", arg("--by"), {"why": arg("--why")})
    print(json.dumps({"action_id": aid, "state": state(aid)}))
elif cmd in ("executed", "failed"):
    aid = rest[0]; need(aid, ["approved"])
    log(aid, cmd, "main-session connector", {"result": json.loads(arg("--result", "{}")) if cmd == "executed" else None, "error": arg("--error")})
    con.execute("UPDATE ledger SET status=? WHERE id=?", (cmd, aid)); con.commit()
    print(json.dumps({"action_id": aid, "state": cmd}))
elif cmd == "outcome":
    aid = rest[0]; need(aid, ["executed"])
    log(aid, "outcome_linked", "outcome-learning", {"expected": arg("--expected"), "actual": arg("--actual"), "variance": arg("--variance")})
    con.execute("UPDATE ledger SET status='outcome_linked' WHERE id=?", (aid,)); con.commit()
    print(json.dumps({"action_id": aid, "state": "outcome_linked"}))
elif cmd == "audit":
    q = "SELECT * FROM action_log" + (" WHERE action_id=?" if rest else "") + " ORDER BY rowid"
    print(json.dumps([dict(r) for r in con.execute(q, tuple(rest[:1]))], indent=1))
