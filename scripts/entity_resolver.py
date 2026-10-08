#!/usr/bin/env python3
"""
entity_resolver.py: cross-source entity resolution, duplicates, conflicts, and staleness.

Works on canonical CSVs produced by normalize.py (or any tables with an id and a name).

USAGE
  python entity_resolver.py --source crm=accounts_crm.csv --source erp=customers_erp.csv \\
      --id account_id --name account_name [--key domain] [--compare industry country annual_revenue] \\
      [--modified last_modified] [--stale-days 180] [--threshold 0.88] [--out resolution.json]

Matching, in order of strength:
  1. exact shared key (--key, e.g. domain or ERP customer number)   confidence 1.00
  2. normalized-name exact match (legal suffixes and punctuation removed)   0.95
  3. fuzzy name similarity >= --threshold (SequenceMatcher)   = similarity score
Fuzzy matches are proposals, never silent merges. Every match carries its method
and confidence.

Also reports:
  duplicates within each source (same normalized name or same key)
  conflicts: matched records whose compared fields disagree (numbers differ by >5%)
  stale records: --modified older than --stale-days
  unmatched records per source (the match rate matters for cross-system metrics)
"""
import argparse, difflib, json, re
import pandas as pd

SUFFIX = r"\b(inc|incorporated|ltd|limited|llc|plc|pvt|private|corp|corporation|co|company|gmbh|ag|sa|bv|nv|llp|group|holdings)\b"


def norm(s):
    """Normalize a company name: lowercase, strip legal suffixes and punctuation."""
    s = re.sub(r"[^a-z0-9 ]", " ", str(s).lower())
    s = re.sub(SUFFIX, " ", s)
    return re.sub(r"\s+", " ", s).strip()


ap = argparse.ArgumentParser()
ap.add_argument("--source", action="append", required=True, help="label=path.csv")
ap.add_argument("--id", required=True)
ap.add_argument("--name", required=True)
ap.add_argument("--key")
ap.add_argument("--compare", nargs="*", default=[])
ap.add_argument("--modified")
ap.add_argument("--stale-days", type=int, default=180)
ap.add_argument("--threshold", type=float, default=0.88)
ap.add_argument("--out")
a = ap.parse_args()

S = {}
for s in a.source:
    lab, path = s.split("=", 1)
    df = pd.read_csv(path)
    df["_norm"] = df[a.name].map(norm)
    S[lab] = df

res = {"sources": {k: int(len(v)) for k, v in S.items()}, "duplicates": {}, "stale": {}, "matches": [],
       "conflicts": [], "unmatched": {}}
now = pd.Timestamp.now()

for lab, df in S.items():
    d = df[df.duplicated("_norm", keep=False) & (df["_norm"] != "")]
    groups = [{"normalized_name": n, "ids": g[a.id].astype(str).tolist()} for n, g in d.groupby("_norm")]
    if a.key and a.key in df:
        dk = df[df[a.key].notna() & df.duplicated(a.key, keep=False)]
        groups += [{"shared_key": str(k), "ids": g[a.id].astype(str).tolist()} for k, g in dk.groupby(a.key)]
    res["duplicates"][lab] = groups
    if a.modified and a.modified in df:
        m = pd.to_datetime(df[a.modified], errors="coerce", format="mixed")
        old = df[(now - m).dt.days > a.stale_days]
        res["stale"][lab] = {"count": int(len(old)), "ids": old[a.id].astype(str).head(50).tolist(),
                             "threshold_days": a.stale_days}

labs = list(S)
for i in range(len(labs)):
    for j in range(i + 1, len(labs)):
        A, Bdf = S[labs[i]], S[labs[j]]
        matched_b = set()
        for _, ra in A.iterrows():
            best, conf, method = None, 0.0, None
            if a.key and a.key in A and a.key in Bdf and pd.notna(ra.get(a.key)):
                hit = Bdf[Bdf[a.key] == ra[a.key]]
                if len(hit):
                    best, conf, method = hit.iloc[0], 1.0, f"shared key '{a.key}'"
            if best is None and ra["_norm"]:
                hit = Bdf[Bdf["_norm"] == ra["_norm"]]
                if len(hit):
                    best, conf, method = hit.iloc[0], 0.95, "normalized name"
            if best is None and ra["_norm"]:
                sims = Bdf["_norm"].map(lambda x: difflib.SequenceMatcher(None, ra["_norm"], x).ratio())
                k = sims.idxmax() if len(sims) else None
                if k is not None and sims[k] >= a.threshold:
                    best, conf, method = Bdf.loc[k], round(float(sims[k]), 3), "fuzzy name (PROPOSED — confirm)"
            if best is None:
                continue
            matched_b.add(best[a.id])
            m = {"a": f"{labs[i]}:{ra[a.id]}", "b": f"{labs[j]}:{best[a.id]}", "name_a": ra[a.name],
                 "name_b": best[a.name], "method": method, "confidence": conf}
            res["matches"].append(m)
            for f in a.compare:
                if f in A and f in Bdf:
                    va, vb = ra.get(f), best.get(f)
                    if pd.isna(va) or pd.isna(vb):
                        continue
                    try:
                        fa, fb = float(va), float(vb)
                        diff = abs(fa - fb) / max(abs(fa), abs(fb), 1e-9) > 0.05
                    except (TypeError, ValueError):
                        diff = str(va).strip().lower() != str(vb).strip().lower()
                    if diff:
                        res["conflicts"].append({"entity": m["a"] + " ↔ " + m["b"], "field": f,
                                                 labs[i]: va, labs[j]: vb})
        res["unmatched"][labs[i]] = int(len(A) - len({x["a"] for x in res["matches"] if x["a"].startswith(labs[i] + ':')}))
        res["unmatched"][labs[j]] = int(len(Bdf) - len(matched_b))

tot = sum(res["sources"].values())
res["match_rate_note"] = "Cross-system metrics should be restricted to matched records if the match rate is below 80%."
res["summary"] = {"matches": len(res["matches"]),
                  "proposed_fuzzy": sum(1 for m in res["matches"] if "PROPOSED" in m["method"]),
                  "conflicts": len(res["conflicts"]),
                  "duplicate_groups": sum(len(v) for v in res["duplicates"].values())}
print(json.dumps(res, indent=2, default=str))
if a.out:
    json.dump(res, open(a.out, "w"), indent=2, default=str)
