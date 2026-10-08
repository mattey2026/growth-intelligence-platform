#!/usr/bin/env python3
"""
domain_delta.py: cross-domain delta detection between two account snapshots (V7.1).

Snapshot format: {"account_id": "...", "as_of": "...", "domains": {"financial_state": {key: {value, source, as_of, corrected?}}, ...}}
(the format produced by twin_state.py snapshot). For each domain it reports new / changed / deleted / corrected
(a changed value whose new record is flagged corrected/restated) / contradictory (multiple sources disagree inside
the new snapshot: key "sources" list with different values). Unchanged domains are listed so they are not recomputed.
USAGE: domain_delta.py prev.json new.json [--out delta.json]
"""
import json, sys
RECOMPUTE = {"financial_state": ["financial-intelligence", "growth-signal-orchestrator"], "marketing_state": ["marketing-intelligence", "growth-signal-orchestrator"],
             "competitive_state": ["competitive-intelligence"], "competitive_threads": ["competitive-thread-intelligence"], "relationship_state": ["relationship-intelligence"],
             "commercial_state": ["deal-intelligence", "growth-opportunity-discovery"], "market_state": ["market-intelligence"], "operational_state": ["customer-digital-twin"]}
P, N = json.load(open(sys.argv[1])), json.load(open(sys.argv[2]))
val = lambda x: x.get("value") if isinstance(x, dict) else x
out = {"account_id": N.get("account_id"), "from": P.get("as_of"), "to": N.get("as_of"), "domains": {}, "unchanged_domains": [], "recompute": {}}
for d in sorted(set(P.get("domains", {})) | set(N.get("domains", {}))):
    p, n = P.get("domains", {}).get(d, {}), N.get("domains", {}).get(d, {})
    new = sorted(set(n) - set(p)); gone = sorted(set(p) - set(n)); changed, corrected, contra = [], [], []
    for k in sorted(set(p) & set(n)):
        if json.dumps(val(p[k]), sort_keys=True, default=str) != json.dumps(val(n[k]), sort_keys=True, default=str):
            item = {"key": k, "from": val(p[k]), "to": val(n[k])}
            (corrected if isinstance(n[k], dict) and (n[k].get("corrected") or n[k].get("restated")) else changed).append(item)
    for k, x in n.items():
        if isinstance(x, dict) and isinstance(x.get("sources"), list) and len({json.dumps(s.get("value"), default=str) for s in x["sources"]}) > 1:
            contra.append({"key": k, "claims": x["sources"]})
    rec = {"new": new, "changed": changed, "deleted": gone, "corrected": corrected, "contradictory": contra}
    if any(rec.values()):
        out["domains"][d] = rec; out["recompute"][d] = RECOMPUTE.get(d, [])
    else:
        out["unchanged_domains"].append(d)
out["summary"] = {d: {k: len(v) for k, v in r.items() if v} for d, r in out["domains"].items()}
print(json.dumps(out, indent=1, default=str))
if "--out" in sys.argv: json.dump(out, open(sys.argv[sys.argv.index("--out") + 1], "w"), indent=1, default=str)
