#!/usr/bin/env python3
"""
data_profiler.py: profile CSV or Excel business files before analysis.

USAGE: python data_profiler.py file.xlsx|file.csv [--sheet NAME] [--out profile.json]

Reports, for every sheet: row and column counts, inferred types, missing-value
rates, duplicate rows, candidate keys, date ranges, numeric summaries with
outliers (IQR rule), low-cardinality categorical values, a guess of the
canonical entity (opportunity, account, invoice, ...), likely relationships
between sheets (shared key values), and data-quality warnings.
Sensitive-looking columns (national IDs, bank or card numbers) are flagged,
and their values are never printed.
"""
import argparse, json, re
import numpy as np
import pandas as pd

ENTITY_HINTS = {
    "opportunity": ["opportunity", "opp", "deal", "stage", "close date", "closedate", "pipeline", "forecast"],
    "account": ["account", "company", "customer", "client", "industry", "domain"],
    "contact": ["contact", "email", "first name", "last name", "phone", "title"],
    "order_transaction": ["invoice", "order", "billing", "payment", "due date", "ar ", "receivable"],
    "case": ["case", "ticket", "incident", "severity", "priority", "sla"],
    "contract": ["contract", "subscription", "renewal", "term", "arr", "mrr"],
    "product": ["product", "sku", "item", "material", "price"],
    "activity": ["activity", "meeting", "call", "task", "event"],
}
SENSITIVE = re.compile(r"(ssn|social security|aadhaar|pan\b|passport|iban|account number|acct no|card number|routing|bank)", re.I)


def infer_type(s):
    """Return a coarse type label for a column."""
    nn = s.dropna()
    if nn.empty:
        return "empty"
    if pd.api.types.is_numeric_dtype(s):
        return "number"
    if pd.api.types.is_datetime64_any_dtype(s):
        return "date"
    sample = nn.astype(str).head(200)
    # Accept a column as numeric if nearly all values parse after stripping currency, commas, and percent.
    if pd.to_numeric(sample.str.replace(r"[,$€£₹%\s]", "", regex=True), errors="coerce").notna().mean() > 0.95:
        return "number_as_text"
    if pd.to_datetime(sample, errors="coerce", format="mixed").notna().mean() > 0.9:
        return "date_as_text"
    return "text"


def profile_sheet(name, df):
    p = {"sheet": name, "rows": int(len(df)), "columns": int(df.shape[1]), "warnings": [], "fields": []}
    df = df.dropna(how="all").dropna(axis=1, how="all")
    dup = int(df.duplicated().sum())
    if dup:
        p["warnings"].append(f"{dup} fully duplicate rows")
    header_text = " ".join(map(str, df.columns)).lower()
    scores = {e: sum(h in header_text for h in hs) for e, hs in ENTITY_HINTS.items()}
    best = max(scores, key=scores.get)
    p["likely_entity"] = best if scores[best] else "unknown"
    p["entity_scores"] = {k: v for k, v in scores.items() if v}
    for c in df.columns:
        s = df[c]
        t = infer_type(s)
        f = {"column": str(c), "type": t, "missing_pct": round(float(s.isna().mean() * 100), 1),
             "distinct": int(s.nunique(dropna=True))}
        if SENSITIVE.search(str(c)):
            f["sensitive"] = True
            p["warnings"].append(f"'{c}' looks sensitive — values masked; confirm it is needed")
            p["fields"].append(f)
            continue
        if f["distinct"] == len(df) and len(df) > 1 and s.notna().all():
            f["candidate_key"] = True
        if t in ("number", "number_as_text"):
            v = pd.to_numeric(s.astype(str).str.replace(r"[,$€£₹%\s]", "", regex=True), errors="coerce") if t == "number_as_text" else s
            v = v.dropna()
            if len(v):
                q1, q3 = v.quantile([.25, .75])
                iqr = q3 - q1
                out = int(((v < q1 - 3 * iqr) | (v > q3 + 3 * iqr)).sum()) if iqr > 0 else 0
                f.update({"min": float(v.min()), "median": float(v.median()), "max": float(v.max()),
                          "sum": float(v.sum()), "outliers_3iqr": out})
                if (v < 0).any():
                    f["negatives"] = int((v < 0).sum())
            if t == "number_as_text":
                p["warnings"].append(f"'{c}' is numeric stored as text")
        elif t in ("date", "date_as_text"):
            d = pd.to_datetime(s, errors="coerce", format="mixed")
            f.update({"min": str(d.min())[:10], "max": str(d.max())[:10], "unparsed": int(s.notna().sum() - d.notna().sum())})
            if d.max() is not pd.NaT and d.max() > pd.Timestamp.now() + pd.Timedelta(days=3650):
                p["warnings"].append(f"'{c}' has dates more than 10 years in the future")
        elif f["distinct"] <= 15:
            f["values"] = {str(k): int(v) for k, v in s.value_counts().head(15).items()}
            # Detect inconsistent spellings: values that differ only by case or whitespace.
            norm = s.dropna().astype(str).str.strip().str.lower()
            if norm.nunique() < s.dropna().astype(str).nunique():
                p["warnings"].append(f"'{c}' has inconsistent spelling/case variants")
        if f["missing_pct"] > 20:
            p["warnings"].append(f"'{c}' is {f['missing_pct']}% empty")
        p["fields"].append(f)
    return p, df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--sheet")
    ap.add_argument("--out")
    a = ap.parse_args()
    if a.file.lower().endswith((".xlsx", ".xlsm", ".xls")):
        sheets = pd.read_excel(a.file, sheet_name=a.sheet or None)
        if isinstance(sheets, pd.DataFrame):
            sheets = {a.sheet: sheets}
    else:
        sheets = {"data": pd.read_csv(a.file)}
    profiles, frames = [], {}
    for n, df in sheets.items():
        p, d = profile_sheet(n, df)
        profiles.append(p)
        frames[n] = d
    # Relationships: columns in different sheets whose values overlap substantially.
    rels = []
    names = list(frames)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            A, B = frames[names[i]], frames[names[j]]
            for ca in A.columns:
                va = set(A[ca].dropna().astype(str))
                if len(va) < 5:
                    continue
                for cb in B.columns:
                    vb = set(B[cb].dropna().astype(str))
                    if len(vb) < 5:
                        continue
                    ov = len(va & vb) / min(len(va), len(vb))
                    if ov >= 0.6:
                        rels.append({"from": f"{names[i]}.{ca}", "to": f"{names[j]}.{cb}", "overlap": round(ov, 2)})
    res = {"file": a.file, "sheets": profiles, "relationships": rels}
    s = json.dumps(res, indent=2, default=str)
    print(s)
    if a.out:
        open(a.out, "w").write(s)


if __name__ == "__main__":
    main()
