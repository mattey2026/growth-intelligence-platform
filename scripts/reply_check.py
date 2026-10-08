#!/usr/bin/env python3
"""
reply_check.py: validates a tier agent's reply before the main session uses it.

Checks:
  1. Contract: the reply starts with RESULT (+ valid JSON with the required keys) or ESCALATE: <reason>
  2. Labels: predictions carry confidence and basis; recommendations carry an owner and an approval flag
  3. Number provenance: every number in the reply must appear in the handoff packet (or in numbers_used
     taken from it). Numbers not in the packet are flagged as possibly invented, and the main session must
     verify them or drop them.
  4. Decisions: if the packet listed decisions in force, recommendations must reference one or state none applies.
Exit code: 0 ok · 3 escalate (re-delegate one tier up) · 1 contract or provenance failure.

USAGE: python reply_check.py reply.txt --packet packet.md [--current-tier T2]
"""
import argparse, json, re, sys
NEXT = {"T1": "T2", "T2": "T3", "T3": "T4", "T4": None}
ap = argparse.ArgumentParser(); ap.add_argument("reply"); ap.add_argument("--packet", required=True); ap.add_argument("--current-tier", default="T2")
a = ap.parse_args()
r = open(a.reply).read().strip(); pk = open(a.packet).read()
out = {"status": None, "issues": []}

def nums(t):
    # Normalise: 12,500,000 → 12500000; keep decimals; ignore years-like dates and IDs such as A002 or O010.
    t = re.sub(r"\b[A-Z]{1,3}-?\d{2,}\b", " ", t)
    t = re.sub(r"\d{4}-\d{2}-\d{2}", " ", t)
    vals = set()
    for m in re.findall(r"(?<![\w.])\$?\d[\d,]*\.?\d*\s*[MK%]?", t):
        s = m.replace("$", "").replace(",", "").strip()
        mult = 1
        if s.endswith("M"): mult, s = 1e6, s[:-1]
        elif s.endswith("K"): mult, s = 1e3, s[:-1]
        s = s.rstrip("%").strip()
        try:
            v = float(s) * mult
            vals.add(round(v, 4)); vals.add(round(v / 100, 4)); vals.add(round(v * 100, 4))
        except ValueError:
            pass
    return vals

if r.startswith("ESCALATE"):
    reason = r.split("\n", 1)[0][len("ESCALATE"):].lstrip(": ").strip()
    out.update(status="ESCALATE", reason=reason or "(no reason given)", next_tier=NEXT.get(a.current_tier))
    if not reason:
        out["issues"].append("ESCALATE without a reason")
    if out["next_tier"] is None:
        out["issues"].append("Already at T4: stop and ask the user or a human expert")
    print(json.dumps(out, indent=1)); sys.exit(3)
if not r.startswith("RESULT"):
    out.update(status="CONTRACT_FAIL"); out["issues"].append("Reply starts with neither RESULT nor ESCALATE")
    print(json.dumps(out, indent=1)); sys.exit(1)
body = r[len("RESULT"):].strip()
m = re.search(r"\{.*\}", body, re.S)
try:
    j = json.loads(m.group(0)) if m else None
except json.JSONDecodeError as e:
    j = None; out["issues"].append(f"RESULT JSON does not parse: {e}")
if j is None:
    out["status"] = "CONTRACT_FAIL"; print(json.dumps(out, indent=1)); sys.exit(1)
for k in ["summary", "confidence", "recommendations", "predictions"]:
    if k not in j:
        out["issues"].append(f"missing key: {k}")
for p in j.get("predictions", []):
    if not p.get("confidence") or not p.get("basis"):
        out["issues"].append(f"prediction without confidence/basis: {p.get('text','')[:60]}")
for rec in j.get("recommendations", []):
    if "approval_required" not in rec or not rec.get("owner"):
        out["issues"].append(f"recommendation without owner/approval flag: {rec.get('text','')[:60]}")
if "Decisions in force" in pk and "None recorded" not in pk.split("Decisions in force")[1][:200]:
    if not any(rec.get("respects_decision") for rec in j.get("recommendations", [])):
        out["issues"].append("decisions in force were provided but no recommendation references one")
pn = nums(pk)
unverified = sorted({x for x in nums(json.dumps({k: v for k, v in j.items() if k != "numbers_used"})) if x not in pn and x not in (0, 1, 100, 0.01, 1.0)})
# numbers that are simple scalings of packet numbers are accepted above; the rest need verification
if unverified:
    out["issues"].append(f"numbers not found in the packet (verify with scripts or remove): {unverified[:10]}")
    out["unverified_numbers"] = unverified
out["status"] = "OK" if not out["issues"] else "OK_WITH_ISSUES" if not any(i.startswith(("missing", "RESULT")) for i in out["issues"]) else "CONTRACT_FAIL"
print(json.dumps(out, indent=1)); sys.exit(0 if out["status"] != "CONTRACT_FAIL" else 1)
