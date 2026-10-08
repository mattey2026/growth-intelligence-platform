#!/usr/bin/env python3
"""
memory_graph.py: persistent Business Memory Graph (SQLite, one portable file).

Memory is structured, not chat history. The store holds:
  facts       temporal facts per entity and attribute: first/last observed, previous value,
              change, rate, status, source, confidence, last verified
  nodes/edges graph of business entities and relationships
  ledger      analyses, predictions, recommendations, decisions, actions, approvals,
              exceptions, assumptions, scenarios, corrections, outcomes, learnings
  alerts      stateful alerts: open / acknowledged / resolved, with last values
  sources     data-source memory: schema hash, rows, last refresh, freshness limit, quality
  runs        analysis log with model-routing metadata (tier, reason, tokens, escalation)
  summaries   compact memory artifacts consumed first by later analyses
  prefs       user preferences (only ones explicitly set)
Status vocabulary: confirmed | inferred | historical | stale | contradicted | unknown

USAGE (all commands print JSON)
  memory_graph.py DB init
  memory_graph.py DB profile-set profile.json                 # business context profile
  memory_graph.py DB profile-get
  memory_graph.py DB facts-ingest facts.json --run RUN        # [{entity,attribute,value,source,confidence,observed_at,status?}]
  memory_graph.py DB delta --since RUN|DATE                   # what changed since
  memory_graph.py DB recall ENTITY --level 1|2|3              # layered, token-efficient retrieval
  memory_graph.py DB record KIND ENTITY "text" [--data JSON] [--run RUN] [--next-review DATE] [--confidence C] [--links ID,...]
  memory_graph.py DB outcome PRED_ID ACTUAL "text" [--learning "rule change"]   # prediction → actual → error
  memory_graph.py DB alert KEY ENTITY CONDITION_TRUE(0/1) --values JSON [--material-pct 5]
  memory_graph.py DB alert-ack KEY
  memory_graph.py DB decisions [--entity E] [--scope TEXT]
  memory_graph.py DB source-register NAME --columns c1,c2 --rows N --refreshed DATE [--max-age-days D] [--quality JSON]
  memory_graph.py DB sources-check --asof DATE
  memory_graph.py DB run-log RUN --question Q --intent I --tier T --reason R --tokens N [--escalated 0/1] [--confidence C]
  memory_graph.py DB summary-write RUN ENTITY summary.json
  memory_graph.py DB compress --stale-days 90 --asof DATE
  memory_graph.py DB pref-set KEY VALUE
  memory_graph.py DB graph-upsert graph.json                  # {"nodes":[{id,type,label,props}], "edges":[{src,rel,dst,props}], "observed_at"}
  memory_graph.py DB neighbors NODE_ID [--depth 2] [--rel REL]  # relationship traversal
  memory_graph.py DB obj-put objects.json                     # V7.1 typed objects (see OBJ_TYPES)
  memory_graph.py DB obj-query [--type T] [--account A] [--competitor C] [--opportunity O] [--since D] [--until D] [--limit N]
  memory_graph.py DB stats
"""
import sys, json, sqlite3, hashlib, argparse
from datetime import datetime, date

SCHEMA = """
CREATE TABLE IF NOT EXISTS profile(id INTEGER PRIMARY KEY CHECK(id=1), data TEXT, updated_at TEXT);
CREATE TABLE IF NOT EXISTS facts(id INTEGER PRIMARY KEY, entity TEXT, attribute TEXT, value TEXT, value_num REAL,
  observed_at TEXT, first_observed TEXT, source TEXT, confidence REAL, status TEXT, is_current INTEGER,
  prev_value TEXT, change REAL, rate_per_30d REAL, run_id TEXT, last_verified TEXT);
CREATE INDEX IF NOT EXISTS f1 ON facts(entity, attribute, is_current);
CREATE TABLE IF NOT EXISTS nodes(id TEXT PRIMARY KEY, type TEXT, label TEXT, props TEXT, first_observed TEXT, last_observed TEXT, status TEXT);
CREATE TABLE IF NOT EXISTS edges(src TEXT, rel TEXT, dst TEXT, props TEXT, first_observed TEXT, last_observed TEXT, status TEXT, PRIMARY KEY(src, rel, dst));
CREATE TABLE IF NOT EXISTS ledger(id TEXT PRIMARY KEY, kind TEXT, entity TEXT, text TEXT, data TEXT, created_at TEXT, run_id TEXT,
  status TEXT, links TEXT, next_review TEXT, confidence REAL);
CREATE TABLE IF NOT EXISTS alerts(key TEXT PRIMARY KEY, entity TEXT, condition TEXT, state TEXT, first_fired TEXT, last_fired TEXT,
  last_values TEXT, times_fired INTEGER, acknowledged_at TEXT);
CREATE TABLE IF NOT EXISTS sources(name TEXT PRIMARY KEY, schema_hash TEXT, columns TEXT, rows INTEGER, last_refresh TEXT,
  max_age_days INTEGER, quality TEXT, status TEXT, limitations TEXT, history TEXT);
CREATE TABLE IF NOT EXISTS runs(run_id TEXT PRIMARY KEY, at TEXT, question TEXT, intent TEXT, tier TEXT, reason TEXT, tokens INTEGER,
  escalated INTEGER, confidence REAL);
CREATE TABLE IF NOT EXISTS summaries(run_id TEXT, entity TEXT, summary TEXT, at TEXT, PRIMARY KEY(run_id, entity));
CREATE TABLE IF NOT EXISTS prefs(key TEXT PRIMARY KEY, value TEXT, set_at TEXT);
CREATE TABLE IF NOT EXISTS domain_objects(obj_id TEXT PRIMARY KEY, obj_type TEXT, tenant TEXT, account_id TEXT, competitor_id TEXT,
  opportunity_id TEXT, observed_at TEXT, recorded_at TEXT, source TEXT, source_date TEXT, confidence REAL, claim_type TEXT, data TEXT);
CREATE INDEX IF NOT EXISTS do1 ON domain_objects(obj_type, account_id, observed_at);
"""

def now():
    return datetime.now().isoformat(timespec="seconds")

def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None

def days(a, b):
    return (datetime.fromisoformat(str(b)[:10]) - datetime.fromisoformat(str(a)[:10])).days

def out(x):
    s = json.dumps(x, indent=1, default=str)
    print(s)

db, cmd, *rest = sys.argv[1:]
con = sqlite3.connect(db)
con.row_factory = sqlite3.Row
con.executescript(SCHEMA)
# V7 tenant isolation: one memory file per tenant. When GROWTH_TENANT is set, the file is bound to that
# tenant on first use, and any other tenant is refused, so data cannot leak between tenants.
import os as _os
con.execute("CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT)")
_t = _os.environ.get("GROWTH_TENANT")
_bound = con.execute("SELECT value FROM meta WHERE key='tenant'").fetchone()
if _t:
    if _bound and _bound[0] != _t:
        print(json.dumps({"error": f"tenant isolation: this memory belongs to tenant '{_bound[0]}', not '{_t}'"})); sys.exit(3)
    if not _bound:
        con.execute("INSERT INTO meta VALUES('tenant', ?)", (_t,)); con.commit()
elif _bound and cmd not in ("stats",):
    print(json.dumps({"error": f"tenant isolation: memory is bound to tenant '{_bound[0]}'; set GROWTH_TENANT"})); sys.exit(3)
q = lambda sql, *p: [dict(r) for r in con.execute(sql, p).fetchall()]

def ledger_id(kind, entity, text):
    return kind[:3].upper() + "-" + hashlib.sha1(f"{kind}{entity}{text}{now()}".encode()).hexdigest()[:8]

if cmd == "init":
    out({"ok": True, "db": db})

elif cmd == "profile-set":
    new = json.load(open(rest[0]))
    old = q("SELECT data FROM profile WHERE id=1")
    res = {"stored": True}
    if old:
        o = json.loads(old[0]["data"])
        # Conflict resolution: never overwrite silently.
        for k in ["business_model", "industry", "business_scale"]:
            ov = o.get(k, {}).get("value") or o.get(k, {}).get("seller_industry")
            nv = new.get(k, {}).get("value") or new.get(k, {}).get("seller_industry")
            if ov != nv:
                lid = ledger_id("conflict", "business", k)
                con.execute("INSERT INTO ledger VALUES(?,?,?,?,?,?,?,?,?,?,?)", (lid, "conflict", "business", f"Profile {k}: {ov} → {nv}",
                            json.dumps({"previous_belief": ov, "new_evidence": new.get(k), "resolution": "new value adopted; previous retained in history"}),
                            now(), None, "resolved", None, None, new.get(k, {}).get("confidence")))
                res.setdefault("transitions", []).append({"field": k, "from": ov, "to": nv, "ledger": lid})
    con.execute("INSERT OR REPLACE INTO profile VALUES(1,?,?)", (json.dumps(new), now()))
    con.commit()
    out(res)

elif cmd == "profile-get":
    r = q("SELECT * FROM profile WHERE id=1")
    out(json.loads(r[0]["data"]) | {"_updated_at": r[0]["updated_at"]} if r else {"profile": None})

elif cmd == "facts-ingest":
    ap = argparse.ArgumentParser(); ap.add_argument("file"); ap.add_argument("--run", default=None)
    a = ap.parse_args(rest)
    F = json.load(open(a.file))
    summary = {"new": [], "changed": [], "unchanged": 0, "conflicts": [], "reconfirmed": 0}
    for f in F:
        e, at, v = f["entity"], f["attribute"], f["value"]
        obs = f.get("observed_at", date.today().isoformat())
        cur = q("SELECT * FROM facts WHERE entity=? AND attribute=? AND is_current=1", e, at)
        vs = json.dumps(v) if not isinstance(v, str) else v
        if not cur:
            con.execute("INSERT INTO facts(entity,attribute,value,value_num,observed_at,first_observed,source,confidence,status,is_current,run_id,last_verified) VALUES(?,?,?,?,?,?,?,?,?,1,?,?)",
                        (e, at, vs, num(v), obs, obs, f.get("source"), f.get("confidence", 1.0), f.get("status", "confirmed"), a.run, obs))
            summary["new"].append(f"{e}.{at}={vs}")
            continue
        c = cur[0]
        if c["value"] == vs:
            con.execute("UPDATE facts SET observed_at=?, last_verified=?, status=CASE WHEN status='stale' THEN 'confirmed' ELSE status END WHERE id=?", (obs, obs, c["id"]))
            summary["unchanged"] += 1; summary["reconfirmed"] += 1
            continue
        chg = rate = None
        if num(v) is not None and num(c["value"]) is not None:
            chg = num(v) - num(c["value"])
            d = max(days(c["observed_at"], obs), 1)
            rate = chg / d * 30
        # Keep history: the old fact becomes historical (or contradicted if it was only inferred).
        con.execute("UPDATE facts SET is_current=0, status=? WHERE id=?", ("contradicted" if c["status"] == "inferred" else "historical", c["id"]))
        con.execute("INSERT INTO facts(entity,attribute,value,value_num,observed_at,first_observed,source,confidence,status,is_current,prev_value,change,rate_per_30d,run_id,last_verified) VALUES(?,?,?,?,?,?,?,?,?,1,?,?,?,?,?)",
                    (e, at, vs, num(v), obs, c["first_observed"], f.get("source"), f.get("confidence", 1.0), f.get("status", "confirmed"), c["value"], chg, rate, a.run, obs))
        item = {"entity": e, "attribute": at, "from": c["value"], "to": vs, "change": chg, "rate_per_30d": None if rate is None else round(rate, 3), "since": c["observed_at"]}
        summary["changed"].append(item)
        if f.get("categorical_conflict") or (num(v) is None and at in ("health", "risk_tier", "renewal_risk", "business_model")):
            lid = ledger_id("conflict", e, at)
            con.execute("INSERT INTO ledger VALUES(?,?,?,?,?,?,?,?,?,?,?)", (lid, "conflict", e, f"{at}: previous belief '{c['value']}' → new evidence '{vs}'",
                        json.dumps({"previous_belief": c["value"], "new_evidence": vs, "evidence_source": f.get("source"), "resolution": "new state adopted; transition recorded"}),
                        now(), a.run, "resolved", None, None, f.get("confidence")))
            summary["conflicts"].append({"entity": e, "attribute": at, "from": c["value"], "to": vs, "ledger": lid})
    con.commit()
    summary["new_count"] = len(summary["new"]); summary["changed_count"] = len(summary["changed"])
    if len(summary["new"]) > 25:
        summary["new"] = summary["new"][:25] + [f"... {summary['new_count'] - 25} more"]
    out(summary)

elif cmd == "delta":
    ap = argparse.ArgumentParser(); ap.add_argument("--since", required=True); a = ap.parse_args(rest)
    if a.since.startswith("RUN") or not a.since[:4].isdigit():
        rows = q("SELECT entity,attribute,prev_value,value,change,rate_per_30d,observed_at,source FROM facts WHERE run_id=? AND prev_value IS NOT NULL", a.since)
        newf = q("SELECT entity,attribute,value FROM facts WHERE run_id=? AND prev_value IS NULL AND first_observed=observed_at", a.since)
    else:
        rows = q("SELECT entity,attribute,prev_value,value,change,rate_per_30d,observed_at,source FROM facts WHERE is_current=1 AND prev_value IS NOT NULL AND observed_at>?", a.since)
        newf = q("SELECT entity,attribute,value FROM facts WHERE is_current=1 AND first_observed>?", a.since)
    led = q("SELECT id,kind,entity,text,created_at FROM ledger WHERE (run_id=? OR created_at>?) ORDER BY created_at", a.since, a.since)
    out({"since": a.since, "changed_facts": rows, "new_facts": len(newf), "ledger_events": led})

elif cmd == "recall":
    ap = argparse.ArgumentParser(); ap.add_argument("entity"); ap.add_argument("--level", type=int, default=1); a = ap.parse_args(rest)
    e = a.entity
    res = {"entity": e, "level": a.level}
    s = q("SELECT run_id,summary,at FROM summaries WHERE entity=? ORDER BY at DESC LIMIT 1", e)
    res["L1_summary"] = json.loads(s[0]["summary"]) | {"_run": s[0]["run_id"], "_at": s[0]["at"]} if s else None
    if a.level >= 2:
        res["L2_open_items"] = {
          "predictions": q("SELECT id,text,confidence,created_at,status,next_review FROM ledger WHERE entity=? AND kind='prediction' AND status!='resolved' ORDER BY created_at DESC LIMIT 5", e),
          "recommendations": q("SELECT id,text,status,created_at FROM ledger WHERE entity=? AND kind='recommendation' ORDER BY created_at DESC LIMIT 5", e),
          "decisions": q("SELECT id,text,created_at,data FROM ledger WHERE (entity=? OR entity='portfolio') AND kind='decision' ORDER BY created_at DESC LIMIT 5", e),
          "actions": q("SELECT id,text,status,created_at FROM ledger WHERE entity=? AND kind='action' ORDER BY created_at DESC LIMIT 5", e),
          "outcomes_learnings": q("SELECT id,kind,text,created_at FROM ledger WHERE entity=? AND kind IN ('outcome','learning') ORDER BY created_at DESC LIMIT 5", e),
          "alerts": q("SELECT key,condition,state,times_fired,last_fired FROM alerts WHERE entity=?", e)}
    if a.level >= 3:
        res["L3_current_state"] = q("SELECT attribute,value,observed_at,status,confidence,source FROM facts WHERE entity=? AND is_current=1", e)
        res["L3_recent_changes"] = q("SELECT attribute,prev_value,value,change,observed_at FROM facts WHERE entity=? AND prev_value IS NOT NULL ORDER BY observed_at DESC LIMIT 10", e)
    res["_approx_tokens"] = len(json.dumps(res, default=str)) // 4
    out(res)

elif cmd == "record":
    ap = argparse.ArgumentParser(); ap.add_argument("kind"); ap.add_argument("entity"); ap.add_argument("text")
    ap.add_argument("--data", default="{}"); ap.add_argument("--run"); ap.add_argument("--next-review"); ap.add_argument("--confidence", type=float)
    ap.add_argument("--links"); ap.add_argument("--status", default="open"); a = ap.parse_args(rest)
    kinds = {"analysis", "prediction", "recommendation", "decision", "action", "approval", "exception", "assumption", "scenario", "correction", "outcome", "learning", "observation"}
    if a.kind not in kinds:
        out({"error": f"kind must be one of {sorted(kinds)}"}); sys.exit(1)
    lid = ledger_id(a.kind, a.entity, a.text)
    con.execute("INSERT INTO ledger VALUES(?,?,?,?,?,?,?,?,?,?,?)", (lid, a.kind, a.entity, a.text, a.data, now(), a.run, a.status, a.links, a.next_review, a.confidence))
    con.commit()
    out({"recorded": lid, "kind": a.kind, "entity": a.entity})

elif cmd == "outcome":
    ap = argparse.ArgumentParser(); ap.add_argument("pred_id"); ap.add_argument("actual", type=float); ap.add_argument("text"); ap.add_argument("--learning"); a = ap.parse_args(rest)
    p = q("SELECT * FROM ledger WHERE id=?", a.pred_id)
    if not p:
        out({"error": "prediction not found"}); sys.exit(1)
    p = p[0]
    predicted = json.loads(p["data"] or "{}").get("probability", p["confidence"])
    err = None if predicted is None else round(a.actual - predicted, 3)
    oid = ledger_id("outcome", p["entity"], a.text)
    con.execute("INSERT INTO ledger VALUES(?,?,?,?,?,?,?,?,?,?,?)", (oid, "outcome", p["entity"], a.text, json.dumps({"prediction_id": a.pred_id, "predicted": predicted, "actual": a.actual, "error": err}), now(), p["run_id"], "closed", a.pred_id, None, None))
    con.execute("UPDATE ledger SET status='resolved' WHERE id=?", (a.pred_id,))
    res = {"outcome": oid, "prediction": a.pred_id, "predicted": predicted, "actual": a.actual, "error": err}
    if a.learning:
        # A learning exists only when it is written down as an explicit rule change.
        lid = ledger_id("learning", p["entity"], a.learning)
        con.execute("INSERT INTO ledger VALUES(?,?,?,?,?,?,?,?,?,?,?)", (lid, "learning", p["entity"], a.learning, json.dumps({"from_outcome": oid, "type": "rule_adjustment", "status": "proposed — apply after review"}), now(), p["run_id"], "proposed", oid, None, None))
        res["learning"] = lid
    con.commit()
    out(res)

elif cmd == "alert":
    ap = argparse.ArgumentParser(); ap.add_argument("key"); ap.add_argument("entity"); ap.add_argument("cond", type=int)
    ap.add_argument("--values", default="{}"); ap.add_argument("--condition-text", default=""); ap.add_argument("--material-pct", type=float, default=5); a = ap.parse_args(rest)
    vals = json.loads(a.values)
    cur = q("SELECT * FROM alerts WHERE key=?", a.key)
    if not a.cond:
        if cur and cur[0]["state"] != "resolved":
            con.execute("UPDATE alerts SET state='resolved', last_values=? WHERE key=?", (json.dumps(vals), a.key)); con.commit()
            out({"key": a.key, "action": "RESOLVED", "message": f"{a.entity}: condition no longer met."})
        else:
            out({"key": a.key, "action": "NONE"})
        sys.exit()
    if not cur or cur[0]["state"] == "resolved":
        con.execute("INSERT OR REPLACE INTO alerts VALUES(?,?,?,?,?,?,?,?,?)", (a.key, a.entity, a.condition_text, "open", now(), now(), json.dumps(vals), 1, None)); con.commit()
        out({"key": a.key, "action": "FIRE_NEW", "message": f"{a.entity}: {a.condition_text}", "values": vals}); sys.exit()
    c = cur[0]
    prev = json.loads(c["last_values"] or "{}")
    moves = {}
    for k, v in vals.items():
        pv = prev.get(k)
        if num(v) is not None and num(pv) is not None and num(pv) != 0 and abs((num(v) - num(pv)) / abs(num(pv)) * 100) >= a.material_pct:
            moves[k] = {"from": pv, "to": v, "pct": round((num(v) - num(pv)) / abs(num(pv)) * 100, 1)}
        elif num(v) is None and v != pv:
            moves[k] = {"from": pv, "to": v}
    if moves:
        con.execute("UPDATE alerts SET last_fired=?, last_values=?, times_fired=times_fired+1 WHERE key=?", (now(), json.dumps(vals), a.key)); con.commit()
        out({"key": a.key, "action": "UPDATE", "state_before": c["state"], "message": f"{a.entity} remains in alert ({a.condition_text}). Since the previous alert on {c['last_fired'][:10]}: " +
             "; ".join(f"{k} {m['from']} → {m['to']}" + (f" ({m['pct']:+}%)" if 'pct' in m else "") for k, m in moves.items()), "changes": moves})
    else:
        out({"key": a.key, "action": "SUPPRESS", "reason": f"state={c['state']}, no material change since {c['last_fired'][:10]}"})

elif cmd == "alert-ack":
    con.execute("UPDATE alerts SET state='acknowledged', acknowledged_at=? WHERE key=?", (now(), rest[0])); con.commit()
    out({"acknowledged": rest[0]})

elif cmd == "decisions":
    ap = argparse.ArgumentParser(); ap.add_argument("--entity"); ap.add_argument("--scope"); a = ap.parse_args(rest)
    rows = q("SELECT id,entity,text,data,created_at,status FROM ledger WHERE kind='decision' ORDER BY created_at DESC")
    if a.entity:
        rows = [r for r in rows if r["entity"] in (a.entity, "portfolio")]
    if a.scope:
        rows = [r for r in rows if a.scope.lower() in (r["text"] + (r["data"] or "")).lower()]
    out(rows)

elif cmd == "source-register":
    ap = argparse.ArgumentParser(); ap.add_argument("name"); ap.add_argument("--columns", required=True); ap.add_argument("--rows", type=int, required=True)
    ap.add_argument("--refreshed", required=True); ap.add_argument("--max-age-days", type=int, default=7); ap.add_argument("--quality", default="{}"); ap.add_argument("--limitations", default="")
    a = ap.parse_args(rest)
    cols = a.columns.split(","); h = hashlib.sha1(",".join(sorted(cols)).encode()).hexdigest()[:10]
    old = q("SELECT * FROM sources WHERE name=?", a.name)
    res = {"source": a.name, "schema_hash": h}
    hist = []
    if old:
        o = old[0]; hist = json.loads(o["history"] or "[]")
        hist.append({"refresh": o["last_refresh"], "rows": o["rows"], "schema_hash": o["schema_hash"]})
        oc = set(json.loads(o["columns"]))
        res.update({"previous_refresh": o["last_refresh"], "rows_change": a.rows - o["rows"], "schema_changed": o["schema_hash"] != h,
                    "columns_added": sorted(set(cols) - oc), "columns_removed": sorted(oc - set(cols)), "version": "updated"})
    else:
        res["version"] = "new"
    con.execute("INSERT OR REPLACE INTO sources VALUES(?,?,?,?,?,?,?,?,?,?)", (a.name, h, json.dumps(cols), a.rows, a.refreshed, a.max_age_days, a.quality, "healthy", a.limitations, json.dumps(hist[-12:])))
    con.commit(); out(res)

elif cmd == "sources-check":
    ap = argparse.ArgumentParser(); ap.add_argument("--asof", default=date.today().isoformat()); a = ap.parse_args(rest)
    res = []
    for s in q("SELECT name,last_refresh,max_age_days,rows,limitations FROM sources"):
        age = days(s["last_refresh"], a.asof)
        st = "Stale" if age > s["max_age_days"] else "Healthy"
        con.execute("UPDATE sources SET status=? WHERE name=?", (st.lower(), s["name"]))
        res.append({"source": s["name"], "last_refreshed": s["last_refresh"], "age_days": age, "status": st, "limitations": s["limitations"]})
    con.commit(); out(res)

elif cmd == "run-log":
    ap = argparse.ArgumentParser(); ap.add_argument("run"); ap.add_argument("--question", default=""); ap.add_argument("--intent", default=""); ap.add_argument("--tier", default="")
    ap.add_argument("--reason", default=""); ap.add_argument("--tokens", type=int, default=0); ap.add_argument("--escalated", type=int, default=0); ap.add_argument("--confidence", type=float)
    a = ap.parse_args(rest)
    con.execute("INSERT OR REPLACE INTO runs VALUES(?,?,?,?,?,?,?,?,?)", (a.run, now(), a.question, a.intent, a.tier, a.reason, a.tokens, a.escalated, a.confidence)); con.commit()
    out({"logged": a.run})

elif cmd == "summary-write":
    run, ent, f = rest
    con.execute("INSERT OR REPLACE INTO summaries VALUES(?,?,?,?)", (run, ent, open(f).read(), now())); con.commit()
    out({"summary": ent, "run": run})

elif cmd == "compress":
    ap = argparse.ArgumentParser(); ap.add_argument("--stale-days", type=int, default=90); ap.add_argument("--asof", default=date.today().isoformat()); ap.add_argument("--keep-history", type=int, default=12)
    a = ap.parse_args(rest)
    before = q("SELECT COUNT(*) n FROM facts")[0]["n"]
    stale = 0
    for f in q("SELECT id,last_verified FROM facts WHERE is_current=1 AND status IN ('confirmed','inferred')"):
        if f["last_verified"] and days(f["last_verified"], a.asof) > a.stale_days:
            con.execute("UPDATE facts SET status='stale' WHERE id=?", (f["id"],)); stale += 1
    # Keep the newest N historical values per entity-attribute; fold older ones into one compressed
    # record (count + range). Decisions, outcomes, and learnings in the ledger are never compressed.
    folded = 0
    for g in q("SELECT entity,attribute,COUNT(*) n FROM facts WHERE is_current=0 GROUP BY entity,attribute HAVING n>?", a.keep_history):
        old = q("SELECT id,value,value_num,observed_at FROM facts WHERE entity=? AND attribute=? AND is_current=0 ORDER BY observed_at DESC", g["entity"], g["attribute"])[a.keep_history:]
        nums = [o["value_num"] for o in old if o["value_num"] is not None]
        con.execute("INSERT INTO facts(entity,attribute,value,observed_at,first_observed,source,status,is_current) VALUES(?,?,?,?,?,?,?,0)",
                    (g["entity"], g["attribute"], json.dumps({"compressed_points": len(old), "min": min(nums) if nums else None, "max": max(nums) if nums else None}),
                     old[0]["observed_at"], old[-1]["observed_at"], "memory-compression", "historical"))
        con.executemany("DELETE FROM facts WHERE id=?", [(o["id"],) for o in old]); folded += len(old)
    con.commit()
    out({"facts_before": before, "facts_after": q("SELECT COUNT(*) n FROM facts")[0]["n"], "marked_stale": stale, "history_points_folded": folded,
         "preserved": "current state, recent history, all decisions, outcomes, learnings, alerts, source history"})

elif cmd == "obj-put":
    # V7.1 typed domain objects: persisted, timestamped, source-linked, confidence-scored, tenant-scoped,
    # queryable by account / time / competitor / opportunity.
    OBJ_TYPES = {"MarketingSignal", "FinancialSignal", "FinancialMetric", "CompetitiveEvent", "CompetitiveThread", "CompetitiveHypothesis",
                 "CompetitiveOutcome", "CampaignInfluence", "AccountEngagement", "CrossDomainPattern", "TwinSnapshot"}
    objs = json.load(open(rest[0])); ten = _os.environ.get("GROWTH_TENANT") or (_bound[0] if _bound else "default")
    bad, n = [], 0
    for o in objs:
        miss = [k for k in ("obj_type", "account_id", "observed_at", "source") if not o.get(k)]
        if o.get("obj_type") not in OBJ_TYPES: miss.append(f"obj_type must be one of {sorted(OBJ_TYPES)}")
        if miss:
            bad.append({"obj": o.get("obj_id"), "missing": miss}); continue
        oid = o.get("obj_id") or o["obj_type"][:3].upper() + "-" + hashlib.sha1(json.dumps(o, sort_keys=True, default=str).encode()).hexdigest()[:10]
        con.execute("INSERT OR REPLACE INTO domain_objects VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)", (oid, o["obj_type"], ten, o["account_id"], o.get("competitor_id"),
                    o.get("opportunity_id"), str(o["observed_at"])[:19], now(), o["source"], o.get("source_date"), o.get("confidence"), o.get("claim_type"),
                    json.dumps(o.get("data", {}), default=str)))
        n += 1
    con.commit(); out({"stored": n, "rejected": bad, "tenant": ten})

elif cmd == "obj-query":
    ap = argparse.ArgumentParser(); ap.add_argument("--type"); ap.add_argument("--account"); ap.add_argument("--competitor"); ap.add_argument("--opportunity")
    ap.add_argument("--since"); ap.add_argument("--until"); ap.add_argument("--limit", type=int, default=500); a = ap.parse_args(rest)
    ten = _os.environ.get("GROWTH_TENANT") or (_bound[0] if _bound else "default")
    w, p = ["tenant=?"], [ten]
    for col, v in [("obj_type", a.type), ("account_id", a.account), ("competitor_id", a.competitor), ("opportunity_id", a.opportunity)]:
        if v: w.append(f"{col}=?"); p.append(v)
    if a.since: w.append("observed_at>=?"); p.append(a.since)
    if a.until: w.append("observed_at<=?"); p.append(a.until)
    rows = q(f"SELECT * FROM domain_objects WHERE {' AND '.join(w)} ORDER BY observed_at LIMIT {int(a.limit)}", *p)
    for r in rows: r["data"] = json.loads(r["data"] or "{}")
    out(rows)

elif cmd == "graph-upsert":
    g = json.load(open(rest[0])); obs = g.get("observed_at", date.today().isoformat())
    seen_n, seen_e = set(), set(); new_n = new_e = 0
    for n in g.get("nodes", []):
        ex = q("SELECT id FROM nodes WHERE id=?", n["id"])
        if ex:
            con.execute("UPDATE nodes SET label=?, props=?, last_observed=?, status='confirmed' WHERE id=?", (n.get("label"), json.dumps(n.get("props", {})), obs, n["id"]))
        else:
            con.execute("INSERT INTO nodes VALUES(?,?,?,?,?,?,?)", (n["id"], n["type"], n.get("label"), json.dumps(n.get("props", {})), obs, obs, "confirmed")); new_n += 1
        seen_n.add(n["id"])
    for e in g.get("edges", []):
        k = (e["src"], e["rel"], e["dst"])
        if q("SELECT 1 FROM edges WHERE src=? AND rel=? AND dst=?", *k):
            con.execute("UPDATE edges SET last_observed=?, props=?, status='confirmed' WHERE src=? AND rel=? AND dst=?", (obs, json.dumps(e.get("props", {})), *k))
        else:
            con.execute("INSERT INTO edges VALUES(?,?,?,?,?,?,?)", (*k, json.dumps(e.get("props", {})), obs, obs, "confirmed")); new_e += 1
        seen_e.add(k)
    # Relationships missing from a full refresh are marked historical, never deleted.
    gone = 0
    if g.get("full_refresh"):
        for e in q("SELECT src,rel,dst FROM edges WHERE status='confirmed'"):
            if (e["src"], e["rel"], e["dst"]) not in seen_e:
                con.execute("UPDATE edges SET status='historical' WHERE src=? AND rel=? AND dst=?", (e["src"], e["rel"], e["dst"])); gone += 1
    con.commit()
    out({"nodes_new": new_n, "edges_new": new_e, "edges_now_historical": gone, "nodes_total": q("SELECT COUNT(*) n FROM nodes")[0]["n"], "edges_total": q("SELECT COUNT(*) n FROM edges")[0]["n"]})

elif cmd == "neighbors":
    ap = argparse.ArgumentParser(); ap.add_argument("node"); ap.add_argument("--depth", type=int, default=1); ap.add_argument("--rel"); a = ap.parse_args(rest)
    frontier, seen, paths = {a.node}, {a.node}, []
    for d in range(a.depth):
        nxt = set()
        for n in frontier:
            for e in q("SELECT src,rel,dst,status FROM edges WHERE (src=? OR dst=?) AND status!='historical'", n, n):
                if a.rel and e["rel"] != a.rel:
                    continue
                o = e["dst"] if e["src"] == n else e["src"]
                paths.append({"depth": d + 1, "from": n, "rel": e["rel"], "to": o})
                if o not in seen:
                    seen.add(o); nxt.add(o)
        frontier = nxt
    nodes = {r["id"]: {"type": r["type"], "label": r["label"]} for r in q(f"SELECT id,type,label FROM nodes WHERE id IN ({','.join('?' * len(seen))})", *seen)}
    out({"node": a.node, "depth": a.depth, "connected": len(seen) - 1, "paths": paths, "nodes": nodes})

elif cmd == "pref-set":
    con.execute("INSERT OR REPLACE INTO prefs VALUES(?,?,?)", (rest[0], rest[1], now())); con.commit(); out({"pref": rest[0], "value": rest[1]})

elif cmd == "stats":
    out({t: q(f"SELECT COUNT(*) n FROM {t}")[0]["n"] for t in ["facts", "nodes", "edges", "ledger", "alerts", "sources", "runs", "summaries", "prefs"]} |
        {"ledger_by_kind": {r["kind"]: r["n"] for r in q("SELECT kind,COUNT(*) n FROM ledger GROUP BY kind")}, "current_facts": q("SELECT COUNT(*) n FROM facts WHERE is_current=1")[0]["n"]})
else:
    out({"error": f"unknown command {cmd}"}); sys.exit(1)
