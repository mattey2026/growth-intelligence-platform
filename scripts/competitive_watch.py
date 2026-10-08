#!/usr/bin/env python3
"""
competitive_watch.py: Competitive Early Warning.

INPUT CSV of competitor observations (from CRM competitor fields, transcripts, RFPs,
proposals, emails, and web, extracted by the skill):
  account_id, competitor, date, source_type (crm|transcript|rfp|email|web|win_loss), strategic (0/1)[, evidence]
USAGE: python competitive_watch.py obs.csv [--period-days 90] [--asof 2026-09-30] [--min-new 3] [--out cw.json]

For each competitor, compares the current period with the prior period:
  accounts_present_now, new_accounts (present now, never seen before in history),
  new_strategic_accounts, mention trend, source diversity (number of independent source types)
Early warning fires when new_strategic_accounts ≥ --min-new, or when new accounts
more than double vs the prior period, or for an emerging competitor (first seen
within the last 2 periods and already in 3 or more accounts).
Example output text: "Competitor X appeared in 7 strategic accounts last quarter where it
previously had no identified presence."
"""
import argparse, json
import pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument("csv")
ap.add_argument("--period-days", type=int, default=90)
ap.add_argument("--asof")
ap.add_argument("--min-new", type=int, default=3)
ap.add_argument("--out")
a = ap.parse_args()
df = pd.read_csv(a.csv)
df["date"] = pd.to_datetime(df.date, errors="coerce", format="mixed")
asof = pd.Timestamp(a.asof) if a.asof else df.date.max()
p = pd.Timedelta(days=a.period_days)
cur = df[(df.date > asof - p) & (df.date <= asof)]
prev = df[(df.date > asof - 2 * p) & (df.date <= asof - p)]
hist = df[df.date <= asof - p]
out = []
for c in sorted(df.competitor.dropna().unique()):
    cc, pc, hc = cur[cur.competitor == c], prev[prev.competitor == c], hist[hist.competitor == c]
    now_acc = set(cc.account_id)
    new = now_acc - set(hc.account_id)
    strat = set(cc[cc.get("strategic", 0) == 1].account_id) if "strategic" in cc else set()
    new_str = new & strat
    prev_new = set(pc.account_id) - set(df[(df.competitor == c) & (df.date <= asof - 2 * p)].account_id)
    first_seen = df[df.competitor == c].date.min()
    emerging = first_seen > asof - 2 * p and len(now_acc) >= 3
    warn = []
    if len(new_str) >= a.min_new:
        warn.append(f"{c} appeared in {len(new_str)} strategic accounts in the last {a.period_days} days where it previously had no identified presence")
    if len(new) >= 2 * max(len(prev_new), 1) and len(new) >= a.min_new:
        warn.append(f"New-account appearances more than doubled ({len(prev_new)} → {len(new)})")
    if emerging:
        warn.append(f"Emerging competitor: first seen {first_seen.date()}, already in {len(now_acc)} accounts")
    out.append({"competitor": c, "accounts_present_now": len(now_acc), "new_accounts": sorted(new),
                "new_strategic_accounts": sorted(new_str), "mentions_now": len(cc), "mentions_prev": len(pc),
                "source_types_now": sorted(cc.source_type.dropna().unique().tolist()) if "source_type" in cc else [],
                "early_warnings": warn,
                "confidence": "High" if cc.source_type.nunique() >= 3 else "Medium" if cc.source_type.nunique() == 2 else "Low"})
out.sort(key=lambda r: (-len(r["early_warnings"]), -len(r["new_strategic_accounts"]), -r["accounts_present_now"]))
res = {"as_of": str(asof.date()), "period_days": a.period_days, "competitors": out,
       "note": "Presence means observed mention or involvement, not confirmed contract. Confidence rises with independent source types."}
print(json.dumps(res, indent=2))
if a.out:
    json.dump(res, open(a.out, "w"), indent=2)
