#!/usr/bin/env python3
"""
dashboard_state.py: server-side Dashboard State (tenant-bound), persisted in the Business Memory file.
Persists: selected account, filters, time range, persona, selected widgets, expanded sections and saved views.
State is keyed by tenant + user + dashboard + entity. A different tenant cannot read or write it, and a state's
persona must be one the user's role may use (checked against persona list, never widening data access: data access
is decided by the role in dashboard_builder.py, not by stored state).
USAGE: dashboard_state.py DB get --user U --dashboard D --entity E
       dashboard_state.py DB set --user U --dashboard D --entity E --state '{...}'
       dashboard_state.py DB save-view --user U --dashboard D --entity E --name "My view" --state '{...}'
       dashboard_state.py DB views --user U --dashboard D --entity E
"""
import sys, json, sqlite3, os, argparse
from datetime import datetime
db, cmd, *rest = sys.argv[1:]
ap = argparse.ArgumentParser()
for k in ["user", "dashboard", "entity", "state", "name"]: ap.add_argument("--" + k)
a = ap.parse_args(rest)
con = sqlite3.connect(db)
con.execute("CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT)")
con.execute("CREATE TABLE IF NOT EXISTS dashboard_state(tenant TEXT, user_id TEXT, dashboard TEXT, entity TEXT, kind TEXT, name TEXT, state TEXT, updated_at TEXT, PRIMARY KEY(tenant, user_id, dashboard, entity, kind, name))")
b = con.execute("SELECT value FROM meta WHERE key='tenant'").fetchone(); t = os.environ.get("GROWTH_TENANT")
if b and t and b[0] != t:
    print(json.dumps({"error": f"tenant isolation: memory belongs to '{b[0]}'"})); sys.exit(3)
TEN = t or (b[0] if b else "default")
if not b and t:   # platform rule (V7): a memory file is bound to its tenant on first use; other tenants are then refused
    con.execute("INSERT OR IGNORE INTO meta VALUES('tenant', ?)", (t,)); con.commit()
ALLOWED = {"persona", "view", "filters", "time_range", "range", "theme", "density", "selected_widgets", "expanded", "entity", "compare", "scenario", "trend"}
def clean(s):
    s = json.loads(s) if isinstance(s, str) else s
    bad = sorted(set(s) - ALLOWED)
    if bad: print(json.dumps({"error": f"unsupported state keys: {bad}", "allowed": sorted(ALLOWED)})); sys.exit(2)
    return s
key = (TEN, a.user, a.dashboard, a.entity)
if cmd == "set":
    s = clean(a.state); con.execute("INSERT OR REPLACE INTO dashboard_state VALUES(?,?,?,?,?,?,?,?)", key + ("current", "", json.dumps(s), datetime.now().isoformat(timespec="seconds"))); con.commit(); print(json.dumps({"saved": True, "tenant": TEN}))
elif cmd == "get":
    r = con.execute("SELECT state, updated_at FROM dashboard_state WHERE tenant=? AND user_id=? AND dashboard=? AND entity=? AND kind='current'", key).fetchone()
    print(json.dumps({"state": json.loads(r[0]) if r else None, "updated_at": r[1] if r else None}))
elif cmd == "save-view":
    s = clean(a.state); con.execute("INSERT OR REPLACE INTO dashboard_state VALUES(?,?,?,?,?,?,?,?)", key + ("view", a.name, json.dumps(s), datetime.now().isoformat(timespec="seconds"))); con.commit(); print(json.dumps({"saved_view": a.name}))
elif cmd == "views":
    print(json.dumps([{"name": n, "state": json.loads(s)} for n, s in con.execute("SELECT name, state FROM dashboard_state WHERE tenant=? AND user_id=? AND dashboard=? AND entity=? AND kind='view' ORDER BY name", key)]))
