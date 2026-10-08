#!/usr/bin/env python3
"""
graph_build.py: builds Memory Graph nodes and edges from a keyed dataset.

Each sheet with its own key (e.g. Opportunity_ID) becomes a node type; a foreign key
(e.g. Account_ID) becomes an edge to that entity. Categorical links named in the
semantic model (Competitor, Product/Offering) become shared nodes, so relationships
across accounts are traversable (for example, which accounts share Competitor B).
USAGE: python graph_build.py data.xlsx --asof DATE [--business-id BIZ] --out graph.json
"""
import argparse, json, re
import pandas as pd
ap = argparse.ArgumentParser(); ap.add_argument("data"); ap.add_argument("--asof", required=True); ap.add_argument("--business-id", default="BUSINESS"); ap.add_argument("--out", required=True)
a = ap.parse_args()
X = {k: v for k, v in pd.read_excel(a.data, sheet_name=None).items() if not re.search(r"readme|test|expected|result|summary|scenario", k, re.I)}
TYPE = {"Account_ID": "account", "Contact_ID": "person", "Opportunity_ID": "opportunity", "Case_ID": "service_case", "Contract_ID": "contract",
        "Campaign_ID": "campaign", "Pricing_Request_ID": "pricing_request", "Pricing_History_ID": "price_point", "Activity_ID": "activity"}
REL = {"person": "WORKS_AT", "opportunity": "OPPORTUNITY_WITH", "service_case": "RAISED_BY", "contract": "CONTRACT_WITH", "campaign": "TARGETS",
       "pricing_request": "PRICING_FOR", "price_point": "PRICED_FOR", "activity": "INTERACTION_WITH"}
N, E = {}, []
N[a.business_id] = {"id": a.business_id, "type": "business", "label": "Business under analysis"}
for s, df in X.items():
    own = next((c for c in df.columns if c in TYPE and df[c].is_unique), None)
    for _, r in df.iterrows():
        if own:
            nid = str(r[own]); t = TYPE[own]
            lab = str(r.get(next((c for c in df.columns if re.search(r"name|issue|campaign|summary", c, re.I)), own), nid))
            props = {f"{s}.{k}" if nid in N else k: (v.item() if hasattr(v, "item") else str(v)) for k, v in r.items() if pd.notna(v) and k != own}
            if nid in N:
                # v7 fix: a later sheet keyed on the same ID (e.g. Finance by Account_ID) MERGES into the node.
                # v6 overwrote it, replacing the account name with its ID.
                N[nid]["props"].update(props)
                if N[nid]["label"] == nid and lab != nid:
                    N[nid]["label"] = lab
            else:
                N[nid] = {"id": nid, "type": t, "label": lab, "props": props}
            if t == "account":
                E.append({"src": a.business_id, "rel": "SERVES", "dst": nid})
            if "Account_ID" in df.columns and own != "Account_ID":
                E.append({"src": nid, "rel": REL.get(t, "RELATES_TO"), "dst": str(r["Account_ID"])})
            if "Opportunity_ID" in df.columns and own not in ("Opportunity_ID",):
                E.append({"src": nid, "rel": "ABOUT_OPPORTUNITY", "dst": str(r["Opportunity_ID"])})
        src = str(r[own]) if own else str(r.get("Account_ID"))
        for col, ntype, rel in [("Primary_Competitor", "competitor", "COMPETES_WITH"), ("Competitor", "competitor", "COMPETES_WITH"),
                                ("Offering", "product", "FOR_PRODUCT"), ("Product", "product", "USES_PRODUCT"), ("Industry", "industry", "IN_INDUSTRY")]:
            if col in df.columns and pd.notna(r[col]) and src != "None":
                pid = f"{ntype}:{r[col]}"
                N.setdefault(pid, {"id": pid, "type": ntype, "label": str(r[col])})
                props = {k: (r[k].item() if hasattr(r[k], "item") else str(r[k])) for k in ["Threat_Level", "Adoption_Index", "Trend", "Estimated_Value"] if k in df.columns and pd.notna(r[k])}
                E.append({"src": src, "rel": rel if s != "Whitespace" else "WHITESPACE_FOR", "dst": pid, "props": props})
uniq = {(e["src"], e["rel"], e["dst"]): e for e in E}
json.dump({"observed_at": a.asof, "full_refresh": True, "nodes": list(N.values()), "edges": list(uniq.values())}, open(a.out, "w"), default=str)
print(json.dumps({"nodes": len(N), "edges": len(uniq), "node_types": pd.Series([n["type"] for n in N.values()]).value_counts().to_dict()}))
