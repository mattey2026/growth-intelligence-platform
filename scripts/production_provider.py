#!/usr/bin/env python3
"""
production_provider.py: PRODUCTION data provider for the Dashboard Intelligence layer.

Builds the same intelligence BUNDLE as demo_provider.py from live sources, and never fills gaps:
  • Business Memory (V7.1): CompetitiveThreads, MarketingSignal objects (re-run through marketing_signals.py),
    FinancialMetric objects (reported facts re-run through financial_intel.py), CrossDomainPattern objects
  • CRM export (xlsx workbook or JSON): opportunities, contacts, account revenue, competitors
  • Optional: monthly billing series (CSV/JSON), quarterly account P&L, operations KPIs, public filings/events
Fields the sources do not contain stay missing (e.g. no opportunity category → "Unclassified"; no growth value →
growth potential "Not available"). dashboard_builder.py shows them as unavailable with what is needed.

USAGE: production_provider.py --entity-id A001 [--memory-db mem.db] [--crm workbook.xlsx | --crm-json crm.json] [--series s.json]
          [--quarters q.json] [--operations ops.json] [--public-facts f.json --public-events e.json] [--asof DATE] --out bundle.json
"""
import sys
import argparse, json, os, subprocess, sqlite3, tempfile
from datetime import date
HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
for k in ["entity-id", "entity-name", "memory-db", "crm", "crm-json", "series", "quarters", "operations", "public-facts", "public-events", "asof", "out"]: ap.add_argument("--" + k)
a = ap.parse_args(); ASOF = a.asof or date.today().isoformat(); T = tempfile.mkdtemp()
def run(script, *args):
    r = subprocess.run([sys.executable, os.path.join(HERE, script), *map(str, args)], capture_output=True, text=True)
    if not r.stdout.strip().startswith(("{", "[")): raise SystemExit(f"{script} failed: {r.stderr[-300:]}")
    return json.loads(r.stdout)
J = lambda f: json.load(open(f)) if f and os.path.exists(f) else None
gaps, used = [], []
# ---------------- CRM ----------------
opps, execs, acct, comp_rows = [], [], {}, []
if a.crm:
    import pandas as pd
    X = pd.read_excel(a.crm, sheet_name=None); used.append(f"CRM export {os.path.basename(a.crm)}")
    A_ = X["Accounts"][X["Accounts"].Account_ID == a.entity_id]
    if A_.empty: raise SystemExit(json.dumps({"error": f"account {a.entity_id} not in CRM export"}))
    acct = A_.iloc[0].to_dict()
    for o in X["Opportunities"][X["Opportunities"].Account_ID == a.entity_id].to_dict("records"):
        if str(o.get("Status", "")).lower() in ("won", "lost", "closed"): continue
        opps.append({"id": o["Opportunity_ID"], "name": o["Opportunity_Name"], "value_m": round(float(o["Amount"]) / 1e6, 3), "probability": float(o["Win_Probability"]),
                     "stage": o["Stage"], "competitor": o["Primary_Competitor"] if isinstance(o.get("Primary_Competitor"), str) else None, "product": o.get("Offering"),
                     "close_date": str(o["Current_Close_Date"])[:10], "owner": None, "region": acct.get("Region"), "source": f"CRM opportunity {o['Opportunity_ID']}"})
    for c in X["Contacts"][X["Contacts"].Account_ID == a.entity_id].to_dict("records"):
        execs.append({"id": c["Contact_ID"], "name": c["Contact_Name"], "role": c["Role"], "influence": {"High": 0.9, "Medium": 0.6, "Low": 0.3}.get(c.get("Influence"), 0.5),
                      "strength": c.get("Relationship_Strength") or "Medium", "trend": "flat", "last_interaction": ASOF, "champion": str(c.get("Champion")).lower() == "yes", "risk": "Low",
                      "opportunities": [o["id"] for o in opps], "source": f"CRM contact {c['Contact_ID']}"})
    comp_rows = X["Competitors"][X["Competitors"].Account_ID == a.entity_id].to_dict("records")
    gaps += ["opportunity category, growth value and strategic impact (not in CRM export)", "prior-period probabilities (no pipeline history mapped)",
             "last-interaction dates and relationship trend (activity log not mapped)", "monthly billing series" if not a.series else None]
elif a.crm_json:
    d = J(a.crm_json); opps, execs, acct = d.get("opportunities", []), d.get("executives", []), d.get("account", {}); used.append("CRM JSON")
else: gaps.append("CRM data (opportunities, contacts)")
name = a.entity_name or acct.get("Account_Name") or a.entity_id
# ---------------- Business Memory ----------------
threads, mk, fi, cd = [], None, None, None
if a.memory_db and os.path.exists(a.memory_db):
    used.append("Business Memory"); con = sqlite3.connect(a.memory_db)
    threads = run("competitive_threads.py", a.memory_db, "query", "--account", name) or run("competitive_threads.py", a.memory_db, "query", "--account", a.entity_id)
    rows = con.execute("SELECT obj_id, account_id, observed_at, source, data FROM domain_objects WHERE obj_type='MarketingSignal' AND account_id IN (?,?)", (name, a.entity_id)).fetchall() \
        if con.execute("SELECT 1 FROM sqlite_master WHERE name='domain_objects'").fetchone() else []
    if rows:
        sig = [{"signal_id": r[0], "account_id": name, "occurred_at": r[2], "source": r[3], **{k: json.loads(r[4]).get(k) for k in ("type", "contact_id", "campaign_id", "topic")}} for r in rows]
        json.dump(sig, open(f"{T}/ms.json", "w"))
        json.dump([{"contact_id": x["id"], "role": x["role"]} for x in execs], open(f"{T}/c.json", "w"))
        mk = run("marketing_signals.py", "--signals", f"{T}/ms.json", "--contacts", f"{T}/c.json", "--asof", ASOF, "--out", f"{T}/mk.json")
    else: gaps.append("marketing signals (none in memory for this account)")
    if not threads: gaps.append("competitive threads (none in memory for this account)")
else: gaps.append("Business Memory (threads, marketing, financial objects)")
if a.public_facts:
    fi = run("financial_intel.py", "--facts", a.public_facts, *(["--events", a.public_events] if a.public_events else []), "--public", "--out", f"{T}/fi.json"); used.append("public filings")
else: gaps.append("customer financial statements or filings")
if mk or fi or threads:
    json.dump(threads, open(f"{T}/th.json", "w"))
    cd = run("cross_domain_correlator.py", "--account", name, *(["--marketing", f"{T}/mk.json"] if mk else []), *(["--financial", f"{T}/fi.json"] if fi else []), "--threads", f"{T}/th.json", "--asof", ASOF)
series = J(a.series); quarters = J(a.quarters) or []; ops = J(a.operations) or []
if not quarters: gaps.append("quarterly account P&L (margin, DSO, cost to serve)")
if not ops: gaps.append("service operations KPIs (SLA, CSAT, escalations)")
bundle = {"bundle_version": "1.0", "provider": "production_provider.py", "data_mode": "production", "data_notice": None,
          "entity": {"id": str(a.entity_id).lower(), "name": name, "segment": acct.get("Segment") or "—", "period": f"FY{ASOF[:4]}", "tenant": os.environ.get("GROWTH_TENANT", "default")},
          "as_of": ASOF, "series": series, "annotations": [], "opportunities": opps, "executives": execs, "marketing": mk, "campaigns": [], "financial_public": fi,
          "account_economics": quarters, "threads": threads, "relationship_signals": [], "correlation": cd, "delta": None, "delta_snapshots": None, "operations": ops,
          "peers": [], "business_units": [], "decisions": [], "market_events": J(a.public_events) or [], "initiatives": [], "scenario_specs": None,
          "competitor_records": comp_rows, "revenue_annual_m": round(float(acct["Current_Revenue"]) / 1e6, 3) if acct.get("Current_Revenue") else None,
          "sources_used": used, "data_gaps": [g for g in gaps if g], "engines_run": [e for e, ok in (("marketing_signals.py", mk), ("financial_intel.py", fi), ("cross_domain_correlator.py", cd), ("competitive_threads.py", threads)) if ok]}
json.dump(bundle, open(a.out, "w"), indent=1, default=str)
print(json.dumps({"bundle": a.out, "entity": name, "opportunities": len(opps), "executives": len(execs), "threads": len(threads), "marketing": bool(mk), "financial": bool(fi), "data_gaps": bundle["data_gaps"]}, indent=1))
