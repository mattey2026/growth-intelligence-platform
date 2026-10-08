#!/usr/bin/env python3
"""
delta_engine.py: dataset recognition and delta-first intelligence.

Compares a NEW dataset with the PREVIOUS version (or with the data-source memory)
and answers, before any expensive analysis:
  What is new? What changed? What disappeared? What was corrected?
  Did the schema change? What requires re-analysis, and by which skills?

USAGE
  python delta_engine.py recognize NEW.xlsx [--memory-db mem.db]
  python delta_engine.py diff PREV.xlsx NEW.xlsx [--material-pct 5] [--emit-facts facts.json] [--out delta.json]

Keys are detected per sheet: the first column named *_ID or ID with unique values.
Row-level diffs cover keyed sheets; for sheets without a key, only row counts and
schema are compared. The re-analysis map ties changed sheets and columns to the
skills whose conclusions depend on them, so only the affected analysis re-runs.
"""
import argparse, json, re, hashlib, sqlite3
import pandas as pd
import numpy as np

REANALYSIS = [  # (sheet or column pattern, skills to re-run)
 (r"opportunit|pipeline|deal", ["deal-intelligence", "pipeline-forecast-intelligence", "daily-growth-briefing"]),
 (r"service|case|incident|ticket", ["customer-digital-twin", "growth-signal-orchestrator", "renewal-expansion-radar"]),
 (r"usage|adoption|product", ["customer-digital-twin", "growth-signal-orchestrator", "growth-opportunity-discovery"]),
 (r"financ|invoice|payment|revenue|margin", ["customer-digital-twin", "account-intelligence-swot-planning", "executive-command-center"]),
 (r"contract|renewal|subscription", ["renewal-expansion-radar", "business-watch"]),
 (r"contact|stakeholder|activit", ["relationship-intelligence", "growth-signal-orchestrator"]),
 (r"pric|discount|benchmark", ["pricing-intelligence"]),
 (r"competit", ["competitive-intelligence"]),
 (r"marketing|campaign|lead", ["growth-opportunity-discovery", "business-intelligence-copilot"]),
 (r"whitespace", ["growth-opportunity-discovery"]),
 (r"account|customer", ["customer-digital-twin", "business-context-discovery"]),
]
SKIP = r"readme|test|expected|result|summary"

def load(p):
    return {k: v for k, v in pd.read_excel(p, sheet_name=None).items() if not re.search(SKIP, k, re.I)} if p.lower().endswith((".xlsx", ".xls", ".xlsm")) else {"data": pd.read_csv(p)}

def key_of(df):
    """Single unique ID column, else a composite key of an ID plus a categorical column (e.g. Account_ID + Product)."""
    for c in df.columns:
        if re.search(r"(^id$|_id$)", str(c), re.I) and df[c].is_unique and df[c].notna().all():
            return c
    ids = [c for c in df.columns if re.search(r"(^id$|_id$)", str(c), re.I)]
    cats = [c for c in df.columns if not pd.api.types.is_numeric_dtype(df[c]) and c not in ids]
    for i in ids:
        for c in cats:
            if not df.duplicated([i, c]).any() and df[[i, c]].notna().all().all():
                return [i, c]
    return None

def fp(df):
    return hashlib.sha1(",".join(map(str, df.columns)).encode()).hexdigest()[:10]

ap = argparse.ArgumentParser()
ap.add_argument("mode", choices=["recognize", "diff"])
ap.add_argument("a")
ap.add_argument("b", nargs="?")
ap.add_argument("--memory-db")
ap.add_argument("--material-pct", type=float, default=5)
ap.add_argument("--emit-facts")
ap.add_argument("--out")
a = ap.parse_args()

if a.mode == "recognize":
    N = load(a.a)
    res = {"sheets": {k: {"rows": len(v), "columns": len(v.columns), "key": key_of(v), "schema_hash": fp(v)} for k, v in N.items()}}
    if a.memory_db:
        con = sqlite3.connect(a.memory_db)
        known = {r[0]: (r[1], r[2], r[3]) for r in con.execute("SELECT name, schema_hash, rows, last_refresh FROM sources")}
        m = {k: ("known, same schema" if k in known and known[k][0] == hashlib.sha1(",".join(sorted(map(str, v.columns))).encode()).hexdigest()[:10]
                 else "known, SCHEMA CHANGED" if k in known else "NEW source") for k, v in N.items()}
        res["memory_match"] = m
        res["verdict"] = ("updated version of a known dataset" if any(v.startswith("known") for v in m.values())
                          else "new dataset — run business-context-discovery")
    print(json.dumps(res, indent=1)); raise SystemExit

P, N = load(a.a), load(a.b)
res = {"sheets": {}, "reanalysis": {}, "materiality": {}}
facts = []
for s in sorted(set(P) | set(N)):
    if s not in N:
        res["sheets"][s] = {"status": "DISAPPEARED"}; continue
    if s not in P:
        res["sheets"][s] = {"status": "NEW", "rows": len(N[s])}; continue
    p, n = P[s], N[s]
    d = {"rows": [len(p), len(n)], "schema_changed": list(p.columns) != list(n.columns),
         "columns_added": sorted(set(map(str, n.columns)) - set(map(str, p.columns))),
         "columns_removed": sorted(set(map(str, p.columns)) - set(map(str, n.columns)))}
    k = key_of(n)
    if k is not None and not all(c in p.columns for c in (k if isinstance(k, list) else [k])):
        k = None
    d["key"] = k
    if k:
        pi, ni = p.set_index(k), n.set_index(k)
        d["added"] = sorted(map(str, set(ni.index) - set(pi.index)))
        d["removed"] = sorted(map(str, set(pi.index) - set(ni.index)))
        common = [c for c in ni.columns if c in pi.columns]
        chg = []
        for idx in sorted(set(ni.index) & set(pi.index), key=str):
            for c in common:
                ov, nv = pi.at[idx, c], ni.at[idx, c]
                if (pd.isna(ov) and pd.isna(nv)) or ov == nv:
                    continue
                item = {"key": "|".join(map(str, idx)) if isinstance(idx, tuple) else str(idx), "column": str(c), "from": None if pd.isna(ov) else (ov.item() if hasattr(ov, "item") else str(ov)),
                        "to": None if pd.isna(nv) else (nv.item() if hasattr(nv, "item") else str(nv))}
                try:
                    fo, fn = float(ov), float(nv)
                    item["pct"] = round((fn - fo) / abs(fo) * 100, 1) if fo else None
                    item["material"] = item["pct"] is None or abs(item["pct"]) >= a.material_pct
                except (TypeError, ValueError):
                    item["material"] = True
                chg.append(item)
        d["changed_cells"] = len(chg); d["changes"] = chg[:60]
        d["status"] = "CHANGED" if chg or d["added"] or d["removed"] or d["schema_changed"] else "UNCHANGED"
        if a.emit_facts:
            for idx, row in ni.iterrows():
                for c in common:
                    v = row[c]
                    if pd.isna(v):
                        continue
                    facts.append({"entity": f"{s}:{'|'.join(map(str, idx)) if isinstance(idx, tuple) else idx}", "attribute": str(c), "value": v.item() if hasattr(v, "item") else str(v), "source": s})
    else:
        same = p.shape == n.shape and p.astype(str).equals(n.astype(str))
        d["status"] = "UNCHANGED" if same else "CHANGED (unkeyed; content differs)"
    res["sheets"][s] = d
    if d["status"] != "UNCHANGED":
        for pat, skills in REANALYSIS:
            if re.search(pat, s, re.I):
                for sk in skills:
                    res["reanalysis"].setdefault(sk, []).append(s)
tot = sum(v.get("changed_cells", 0) for v in res["sheets"].values() if isinstance(v, dict))
mat = sum(1 for v in res["sheets"].values() if isinstance(v, dict) for c in v.get("changes", []) if c.get("material"))
res["materiality"] = {"changed_cells": tot, "material_changes": mat,
                      "sheets_changed": [k for k, v in res["sheets"].items() if v.get("status", "").startswith(("CHANGED", "NEW", "DISAPPEARED"))],
                      "sheets_unchanged": [k for k, v in res["sheets"].items() if v.get("status") == "UNCHANGED"]}
res["decision"] = ("NO RE-ANALYSIS: reuse previous conclusions" if mat == 0 and not any(v.get("added") or v.get("removed") for v in res["sheets"].values() if isinstance(v, dict))
                   else f"PARTIAL RE-ANALYSIS: re-run {len(res['reanalysis'])} skills on {len(res['materiality']['sheets_changed'])} changed sheets; reuse the rest")
if a.emit_facts:
    json.dump(facts, open(a.emit_facts, "w"), default=str)
    res["facts_emitted"] = len(facts)
print(json.dumps(res, indent=1, default=str))
if a.out:
    json.dump(res, open(a.out, "w"), indent=1, default=str)
