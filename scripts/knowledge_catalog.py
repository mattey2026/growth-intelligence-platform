#!/usr/bin/env python3
"""
knowledge_catalog.py: Enterprise Knowledge Intelligence catalogue.

INPUT CSV of documents (metadata listed from SharePoint, Confluence, Drive, and similar,
by the connected tools):
  doc_id, title, source (sharepoint|confluence|gdrive|kb|crm|upload), doc_type (policy|contract|proposal|
  product_doc|collateral|kb_article|presentation|pricing|security), modified (date), owner,
  status (approved|published|draft|archived|unknown)[, version, url, topic]
USAGE: python knowledge_catalog.py docs.csv [--stale-days 365] [--similar 0.85] [--topic pricing] [--out catalog.json]

Produces:
  version_groups  documents with near-identical titles (after removing version, date, and "final"
                  tokens), with the authoritative one chosen by: status (approved > published >
                  draft > unknown > archived), then the most recent modified date
  authority_rank  per document, a 0-100 score from status, doc_type authority (policy/contract/pricing high;
                  collateral/presentation low), freshness, and source (system of record > personal drive)
  stale           not modified within --stale-days, or archived and still referenced
  conflict_candidates  groups where two or more non-archived versions are both "approved/published"
                  (competing truths; content-level conflicts are then checked by the skill)
Access control is enforced by the connectors: only documents the user can open are listed.
"""
import argparse, difflib, json, re
import pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument("csv")
ap.add_argument("--stale-days", type=int, default=365)
ap.add_argument("--similar", type=float, default=0.85)
ap.add_argument("--topic")
ap.add_argument("--out")
a = ap.parse_args()
df = pd.read_csv(a.csv)
if a.topic and "topic" in df:
    df = df[df.topic.astype(str).str.contains(a.topic, case=False) | df.title.str.contains(a.topic, case=False)]
df["modified"] = pd.to_datetime(df.modified, errors="coerce", format="mixed")
now = pd.Timestamp.now()
ST = {"approved": 4, "published": 3, "draft": 1, "unknown": 1, "archived": 0}
DT = {"policy": 25, "contract": 25, "pricing": 25, "security": 20, "product_doc": 18, "kb_article": 15, "proposal": 12,
      "presentation": 8, "collateral": 8}
SRC = {"crm": 10, "sharepoint": 10, "confluence": 10, "kb": 10, "gdrive": 6, "upload": 3}


def key(t):
    """Title with version, date, and 'final/copy/draft' tokens removed."""
    t = t.lower()
    t = re.sub(r"\b(v|ver|version)\s*\d+(\.\d+)*\b|\b(final|draft|copy|latest|new|updated)\b|\d{4}[-_/]\d{1,2}([-_/]\d{1,2})?|[_\-()]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


df["k"] = df.title.map(key)
df["age_days"] = (now - df.modified).dt.days
df["authority"] = (df.status.map(ST).fillna(1) * 10 + df.doc_type.map(DT).fillna(8) + df.source.map(SRC).fillna(5)
                   + (25 - (df.age_days.clip(0, 730) / 730 * 25))).round(0).clip(0, 100)
groups, used = [], set()
for i, r in df.iterrows():
    if i in used:
        continue
    g = [j for j, s in df.iterrows() if j not in used and difflib.SequenceMatcher(None, r.k, s.k).ratio() >= a.similar]
    used |= set(g)
    if len(g) > 1:
        gg = df.loc[g].sort_values(["status", "modified"], key=lambda c: c.map(ST) if c.name == "status" else c, ascending=False)
        live = gg[gg.status.isin(["approved", "published"])]
        groups.append({"title_key": r.k, "authoritative": gg.iloc[0].doc_id,
                       "versions": gg[["doc_id", "title", "status", "modified", "source"]].astype(str).to_dict("records"),
                       "conflict_candidate": len(live) >= 2})
stale = df[(df.age_days > a.stale_days) & (df.status != "archived")]
res = {"documents": len(df), "version_groups": groups,
       "conflict_candidates": [g["title_key"] for g in groups if g["conflict_candidate"]],
       "stale": stale[["doc_id", "title", "age_days", "status"]].astype(str).to_dict("records"),
       "authority_rank": df.sort_values("authority", ascending=False)[["doc_id", "title", "doc_type", "status", "authority"]].astype(str).head(25).to_dict("records")}
print(json.dumps(res, indent=2, default=str))
if a.out:
    json.dump(res, open(a.out, "w"), indent=2, default=str)
