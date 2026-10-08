#!/usr/bin/env python3
"""
policy_gate.py: Policy / Governance Gate + Human Approval Gate.

Evaluates a requested action (or data access) BEFORE execution:
  tenant isolation → agent permission (registry) → agent autonomy vs catalog → user RBAC (role inheritance)
  → ABAC attributes (e.g. region) → data sensitivity vs clearance → evidence sufficiency → risk / approval rule
Decision: ALLOW | REQUIRE_APPROVAL(approver) | DENY, with every rule that fired (for the audit trail).
Agents inherit the USER's permissions: an agent never gains access because another agent or the platform has it.

USAGE
  python policy_gate.py ROOT --tenant-policy policy.yaml --request request.json
request.json: {"tenant": "demo-tenant", "user": {"id": "u1", "role": "seller", "region": "EMEA"},
  "agent": "deal-strategy-agent", "action": "email.send" | null, "data": ["crm"], "sensitivity": ["pii"],
  "record": {"region": "EMEA", "owner": "u1"}, "evidence": {"confidence": 0.72, "items": 3}}
"""
import argparse, json, sys, yaml, re
ap = argparse.ArgumentParser(); ap.add_argument("root"); ap.add_argument("--tenant-policy", required=True); ap.add_argument("--request", required=True)
a = ap.parse_args()
cat = yaml.safe_load(open(f"{a.root}/policy/action-catalog.yaml"))["actions"]
pol = yaml.safe_load(open(a.tenant_policy)); req = json.load(open(a.request))
reg = {m["id"]: m for m in json.load(open(f"{a.root}/registry/agent-registry.json"))["agents"]}
fired, decision, approver = [], "ALLOW", None
def deny(why):
    print(json.dumps({"decision": "DENY", "reasons": fired + [why]}, indent=1)); sys.exit(2)

if req.get("tenant") != pol["tenant_id"]:
    deny(f"tenant mismatch: request {req.get('tenant')} vs policy {pol['tenant_id']} (tenant isolation)")
fired.append("tenant ok")
role = req["user"]["role"]; R = pol["roles"]
if role not in R: deny(f"unknown role {role}")
def eff(r, key):
    v = set(R[r].get(key, []))
    if "inherits" in R[r]: v |= eff(R[r]["inherits"], key)
    return v
u_actions, u_data, u_clear = eff(role, "actions"), eff(role, "data"), eff(role, "clearance")
ag = reg.get(req.get("agent"))
if not ag: deny(f"agent {req.get('agent')} not in registry")
if ag["status"] in ("DISABLED", "DEPRECATED"): deny(f"agent {ag['id']} is {ag['status']}")
fired.append(f"agent {ag['id']} {ag['status']} L{ag['autonomy_level']}")
for d in req.get("data", []):
    if d not in u_data: deny(f"user role '{role}' has no access to data source '{d}' (agents inherit user permissions)")
    if ag["runtime"] != "main-session" and not any(d == x or x.startswith(d) or d.startswith(x.split("_")[0]) for x in ag["data_access"]):
        deny(f"agent {ag['id']} is not allowed data source '{d}' (least privilege)")
fired.append("data access ok")
for s in req.get("sensitivity", []):
    if s not in u_clear: deny(f"data class '{s}' exceeds the clearance of role '{role}'")
for rule in pol.get("abac", []):
    attr = rule["attribute"]
    rec, usr = req.get("record", {}), req["user"]
    if attr in rec and attr in usr and usr[attr] != rec[attr] and role not in ("cro", "cfo", "ceo"):
        deny(f"ABAC: user.{attr}={usr[attr]} but record.{attr}={rec[attr]}")
fired.append("ABAC ok")
act = req.get("action")
if act:
    c = cat.get(act)
    if not c: deny(f"action '{act}' is not in the catalog (only catalog actions can execute)")
    if c["approval"] == "human_only": deny(f"'{act}' is human-only: the platform never executes it")
    if act not in u_actions: deny(f"role '{role}' may not perform '{act}'")
    if ag["runtime"] != "main-session" and not any(act.split("(")[0] in p for p in ag.get("action_permissions", []) + ["prepare any catalog action"]) and "prepare any catalog action" not in " ".join(ag.get("action_permissions", [])):
        deny(f"agent {ag['id']} has no permission to prepare '{act}'")
    if ag["autonomy_level"] < c["autonomy"]: deny(f"agent autonomy L{ag['autonomy_level']} below required L{c['autonomy']}")
    ev = req.get("evidence", {})
    if ev.get("confidence", 0) < pol["min_evidence_confidence"] or ev.get("items", 0) < pol["min_evidence_items"]:
        deny(f"evidence insufficient for action (confidence {ev.get('confidence')} < {pol['min_evidence_confidence']} or items {ev.get('items')} < {pol['min_evidence_items']})")
    fired.append("evidence sufficient")
    level = min(ag["autonomy_level"] if ag["runtime"] != "main-session" else 3, pol["max_autonomy_level"])
    if pol.get("auto_execute_low_risk") and c["risk"] == "low" and not c["external"]:
        level = max(level, 3) if pol["max_autonomy_level"] >= 3 else level
    if c["approval"] == "none" or (level <= c["auto_max"] and c["risk"] == "low" and not c["external"] and c["approval"] in ("none", "user") and pol.get("auto_execute_low_risk")):
        decision = "ALLOW"; fired.append(f"{act}: risk {c['risk']}, no per-item approval needed at L{level}")
    else:
        decision = "REQUIRE_APPROVAL"; approver = c["approval"] if c["approval"] != "record_owner" else f"record_owner ({req.get('record', {}).get('owner', 'unknown')})"
        fired.append(f"{act}: risk {c['risk']}{', external' if c['external'] else ''} → approval by {approver}")
print(json.dumps({"decision": decision, "approver": approver, "reasons": fired}, indent=1))
sys.exit(0)
