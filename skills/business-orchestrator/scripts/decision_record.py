#!/usr/bin/env python3
"""
decision_record.py: Decision Intelligence record (Executive Decision Agent → Decision Memory).

Validates a decision memo against the required structure and stores it as a `decision` in memory ONLY when
the owner approves (status approved). Proposed memos are stored as `scenario` entries (status proposed)
so they can be challenged.
Required fields: situation, options[{name, summary, financial_impact, strategic_impact, risks, dependencies}],
evidence[], trade_offs, recommendation, confidence, what_would_change, decision_owner, decision_deadline,
required_approval, (optional) challenge {steelman_alternative, missing_information, downside}
USAGE: decision_record.py DB validate memo.json | propose memo.json --entity E | approve DEC_PROPOSAL_ID --by owner
"""
import sys, json, sqlite3, hashlib
from datetime import datetime
REQ = ["situation", "options", "evidence", "trade_offs", "recommendation", "confidence", "what_would_change", "decision_owner", "decision_deadline", "required_approval"]
OPT = ["name", "summary", "financial_impact", "strategic_impact", "risks", "dependencies"]
db, cmd, *rest = sys.argv[1:]
def check(m):
    e = [f"missing {k}" for k in REQ if not m.get(k)]
    if len(m.get("options", [])) < 2: e.append("at least 2 options required (including 'do nothing' or the status quo)")
    for o in m.get("options", []):
        e += [f"option '{o.get('name')}' missing {k}" for k in OPT if k not in o]
    if isinstance(m.get("confidence"), (int, float)) and m["confidence"] > 0.9 and len(m.get("evidence", [])) < 3:
        e.append("high confidence with thin evidence: lower the confidence or add evidence")
    return e
con = sqlite3.connect(db); now = datetime.now().isoformat(timespec="seconds")
if cmd == "validate":
    e = check(json.load(open(rest[0]))); print(json.dumps({"valid": not e, "issues": e}, indent=1)); sys.exit(0 if not e else 1)
elif cmd == "propose":
    m = json.load(open(rest[0])); e = check(m)
    if e: print(json.dumps({"refused": e})); sys.exit(1)
    ent = rest[rest.index("--entity") + 1] if "--entity" in rest else "portfolio"
    pid = "DPR-" + hashlib.sha1((m["situation"] + now).encode()).hexdigest()[:8]
    con.execute("INSERT INTO ledger(id,kind,entity,text,data,created_at,status,confidence) VALUES(?,?,?,?,?,?,?,?)",
                (pid, "scenario", ent, "Decision proposal: " + m["recommendation"][:120], json.dumps(m), now, "proposed", m.get("confidence") if isinstance(m.get("confidence"), (int, float)) else None))
    con.commit(); print(json.dumps({"proposal": pid, "status": "proposed", "owner": m["decision_owner"], "deadline": m["decision_deadline"]}))
elif cmd == "approve":
    pid = rest[0]; by = rest[rest.index("--by") + 1]
    r = con.execute("SELECT entity,data FROM ledger WHERE id=? AND status='proposed'", (pid,)).fetchone()
    if not r: print(json.dumps({"error": "no proposed decision with that id"})); sys.exit(1)
    m = json.loads(r[1])
    if by.lower() not in str(m["decision_owner"]).lower():
        print(json.dumps({"error": f"only the decision owner ({m['decision_owner']}) can approve"})); sys.exit(1)
    did = "DEC-" + pid[4:]
    con.execute("INSERT INTO ledger(id,kind,entity,text,data,created_at,status,links) VALUES(?,?,?,?,?,?,?,?)",
                (did, "decision", r[0], m["recommendation"], json.dumps({**m, "approved_by": by, "approved_at": now}), now, "in_force", pid))
    con.execute("UPDATE ledger SET status='decided' WHERE id=?", (pid,)); con.commit()
    print(json.dumps({"decision": did, "status": "in_force", "approved_by": by}))
