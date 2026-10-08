#!/usr/bin/env python3
"""
context_discovery.py: Layer 0 Business Context Discovery.

Infers, from the data itself (never from a single field):
  business model   B2B, B2G, B2C, D2C, B2B2C, C2C, B2E, C2B, G2C, G2G, hybrid
  industry         the SELLER's industry (what the business sells), kept separate from
                   the industries of its CUSTOMERS
  business scale   from financial, commercial, organizational, and operational dimensions
  revenue model, sales motion, customer model, geography, and the primary KPI framework
Every conclusion carries a confidence score and its evidence. When confidence is below
--min-confidence, the output sets "needs_clarification" and lists targeted questions.

USAGE: python context_discovery.py data.xlsx|a.csv [b.csv ...] [--min-confidence 0.6] [--out profile.json]
"""
import argparse, json, re, os
import pandas as pd
import numpy as np

def load(paths):
    T = {}
    for p in paths:
        if p.lower().endswith((".xlsx", ".xlsm", ".xls")):
            for k, v in pd.read_excel(p, sheet_name=None).items():
                T[k] = v
        else:
            T[os.path.splitext(os.path.basename(p))[0]] = pd.read_csv(p)
    return T

KW = {  # evidence keywords: sheet names, column names, and categorical values
 "B2B": ["account", "opportunit", "pipeline", "proposal", "negotiation", "rfp", "procurement", "cio", "cfo", "coo", "cto",
         "vp ", "executive sponsor", "champion", "contract", "renewal", "enterprise", "mid-market", "decision", "stakeholder", "sla"],
 "B2G": ["agency", "ministry", "department of", "tender", "award", "bid", "government", "public sector", "municipal", "federal", "grant"],
 "B2C": ["consumer", "shopper", "order", "basket", "cart", "sku", "aov", "return", "loyalty", "store visit", "customer_id", "household"],
 "D2C": ["direct-to-consumer", "d2c", "shopify", "website order", "website", "instagram", "app store", "subscription box", "roas", "checkout", "ecommerce", "e-commerce"],
 "B2B2C": ["reseller", "distributor", "retailer", "end consumer", "end_consumer", "sell-through", "sell_through", "sell_in", "partner channel", "partner_id", "wholesale", "reseller_margin"],
 "C2C": ["seller_id", "buyer_id", "listing", "marketplace", "peer", "gmv", "take rate"],
 "B2E": ["employee benefit", "payroll", "workforce", "staff portal", "internal customer"],
 "G2C": ["citizen", "permit", "license application", "benefit claim", "taxpayer"],
 "C2B": ["creator", "freelancer", "influencer payout", "contributor"],
 "G2G": ["inter-agency", "state government", "federal transfer"]}
SELLER_INDUSTRY = {  # offering vocabulary → the seller's industry
 "Technology & IT Services": ["ai services", "cloud", "analytics", "data", "platform", "devops", "automation", "digital", "technology", "software", "saas", "managed services", "services"],
 "Healthcare Provider": ["patient", "admission", "claim", "clinic", "bed", "physician"],
 "Retail / Consumer Goods": ["sku", "store", "basket", "merchandise", "apparel"],
 "Financial Services": ["loan", "deposit", "premium", "policy", "portfolio", "aum"],
 "Manufacturing": ["bill of materials", "plant", "work order", "yield", "production line"]}

def text_of(T):
    parts = []
    for name, df in T.items():
        parts.append(name.lower())
        parts += [str(c).lower() for c in df.columns]
        for c in df.columns:
            if not pd.api.types.is_numeric_dtype(df[c]) and df[c].nunique() <= 60:
                parts += [str(v).lower() for v in df[c].dropna().unique()]
    return " | ".join(parts)

def find(T, pat):
    """Find the first numeric column whose name matches pat; return (sheet, column, series)."""
    for n, df in T.items():
        for c in df.columns:
            if re.search(pat, str(c), re.I) and pd.api.types.is_numeric_dtype(df[c]):
                return n, c, df[c].dropna()
    return None, None, None

ap = argparse.ArgumentParser()
ap.add_argument("paths", nargs="+")
ap.add_argument("--min-confidence", type=float, default=0.6)
ap.add_argument("--out")
a = ap.parse_args()
T = {k: v for k, v in load(a.paths).items() if not re.search(r"readme|test|expected|result", k, re.I)}
txt = text_of(T)

# ---- business model
scores, ev = {}, {}
for m, kws in KW.items():
    hits = sorted({k.strip() for k in kws if re.search(r"(?<![a-z])" + re.escape(k.strip()) + r"(?![a-z])" if len(k.strip()) <= 4 else re.escape(k.strip()), txt)})
    scores[m] = len(hits)
    ev[m] = hits
n_cust = max((df.iloc[:, 0].nunique() for n, df in T.items() if re.search(r"account|customer|client", n, re.I)), default=None)
_, rcol, rev = find(T, r"revenue|arr|contract_value|annual")
_, dcol, deal = find(T, r"^amount$|deal.?value|deal.?size|opportunity.?amount")
structural = []
if n_cust and rev is not None and len(rev):
    rpc = float(rev.mean())
    structural.append(f"{n_cust} customers, mean revenue per customer ${rpc:,.0f}")
    if rpc > 250_000:
        scores["B2B"] += 3; structural.append("high revenue per customer → organizational buyers")
    elif rpc < 2_000:
        scores["B2C"] += 3; structural.append("low revenue per customer → individual consumers")
if deal is not None and len(deal):
    structural.append(f"median deal ${float(deal.median()):,.0f} across {len(deal)} deals")
    if deal.median() > 100_000:
        scores["B2B"] += 2
roles = [str(v).lower() for n, df in T.items() for c in df.columns if re.search(r"role|title", str(c), re.I) for v in df[c].dropna().unique()]
exec_roles = [r for r in roles if re.search(r"\b(cio|cfo|coo|cto|ceo|chief|vp|director|head|sponsor|procurement)\b", r)]
if exec_roles:
    scores["B2B"] += 2; structural.append(f"buyer roles are corporate ({len(exec_roles)} executive or functional roles)")
tot = sum(scores.values()) or 1
ranked = sorted(scores.items(), key=lambda kv: -kv[1])
top, second = ranked[0], ranked[1]
conf = round(min(0.98, (top[1] / tot) * 0.6 + (min(top[1] - second[1], 10) / 10) * 0.4), 2)
# D2C is a B2C subtype: a consumer business selling its own brand through its own channels.
if top[0] == "B2C" and scores["D2C"] >= 1:
    scores["D2C"] += scores["B2C"]; ev["D2C"] = ev["D2C"] + ev["B2C"] + ["consumer business selling through its own channels → D2C"]
    ranked = sorted(scores.items(), key=lambda kv: -kv[1]); top, second = ranked[0], ranked[1]
    conf = round(min(0.98, (top[1] / sum(scores.values())) * 0.6 + (min(top[1] - second[1], 10) / 10) * 0.4), 2)
secondary = [m for m, s in ranked[1:] if s >= max(3, 0.4 * top[1]) and not (top[0] == "D2C" and m == "B2C")]
model = "Undetermined" if top[1] == 0 else (top[0] if not secondary else f"Hybrid ({top[0]} primary; {', '.join(secondary)})")

# ---- industry: the seller's industry, separate from its customers'
off_cols = [df[c] for n, df in T.items() for c in df.columns if re.search(r"offering|product|service_line|sku", str(c), re.I) and not pd.api.types.is_numeric_dtype(df[c])]
offer_txt = " | ".join(" ".join(map(str, s.dropna().unique())).lower() for s in off_cols)
ind_scores = {k: sum(1 for w in v if w in offer_txt) for k, v in SELLER_INDUSTRY.items()}
ind = max(ind_scores, key=ind_scores.get)
ind_conf = round(min(0.95, ind_scores[ind] / 8), 2) if ind_scores[ind] else 0.0
cust_ind = [df[c] for n, df in T.items() if re.search(r"account|customer", n, re.I) for c in df.columns if re.search(r"industry|sector|vertical", str(c), re.I)]
cust_mix = cust_ind[0].value_counts().to_dict() if cust_ind else {}
offerings = sorted({o for s in off_cols for o in s.dropna().astype(str).unique()})
has_services = any(re.search(r"service", o, re.I) for o in offerings)
has_product = any(re.search(r"platform|cloud|software|ai|analytics|data|technology", o, re.I) for o in offerings)
sub = ("Enterprise technology — hybrid software + professional/managed services" if has_services and has_product
       else "Enterprise software" if has_product else "Professional services" if has_services else "Undetermined")

# ---- scale: several dimensions, never deal size alone
dims, flags = {}, []
if rev is not None:
    dims["financial_revenue_in_dataset"] = float(rev.sum())
    flags.append("revenue ≥ $50M" if rev.sum() >= 50e6 else "revenue < $50M")
if deal is not None:
    dims["commercial_median_deal"] = float(deal.median())
seg_vals = [str(v).lower() for n, df in T.items() for c in df.columns if re.search(r"segment|tier", str(c), re.I) for v in df[c].dropna().unique()]
dims["commercial_customer_segments"] = sorted(set(seg_vals))
regions = sorted({str(v) for n, df in T.items() for c in df.columns if re.search(r"^region$|country|geo", str(c), re.I) for v in df[c].dropna().unique()})
dims["organizational_regions"] = regions
dims["commercial_stakeholder_roles"] = len(set(roles))
dims["operational_entities"] = {n: len(df) for n, df in T.items()}
dims["employee_count"] = "not in data"
pts = 0
pts += 2 if dims.get("financial_revenue_in_dataset", 0) >= 50e6 else 0
pts += 1 if dims.get("commercial_median_deal", 0) >= 1e6 else 0
pts += 1 if len(regions) >= 3 else 0
pts += 1 if "enterprise" in " ".join(dims["commercial_customer_segments"]) else 0
pts += 1 if dims["commercial_stakeholder_roles"] >= 8 else 0
scale = ("Large Enterprise" if pts >= 5 and dims.get("financial_revenue_in_dataset", 0) >= 250e6 else
         "Enterprise" if pts >= 4 else "Mid-Market" if pts >= 2 else "SMB / Small Mid-Market")
scale_conf = round(0.45 + 0.08 * pts - (0.15 if dims["employee_count"] == "not in data" else 0), 2)

# ---- revenue model and sales motion
renew = any(re.search(r"renewal|expiry|subscription|contract", n + " ".join(map(str, df.columns)), re.I) for n, df in T.items())
stages = any(re.search(r"stage", " ".join(map(str, df.columns)), re.I) for df in T.values())
revenue_model = "Contracted / recurring (renewals present) + project revenue" if renew else "Transactional"
sales_motion = ("Field / enterprise sales (staged pipeline, proposals, negotiation, executive engagement)" if stages and exec_roles
                else "Self-serve / transactional" if scores["B2C"] + scores["D2C"] > scores["B2B"] else "Undetermined")

KPI = {"B2B": {"primary": ["Contracted revenue (ARR-like)", "Net / gross revenue retention", "Pipeline and weighted pipeline", "Pipeline coverage", "Win rate", "Average deal size (ACV)", "Gross margin and contribution", "Renewal exposure", "Revenue concentration"],
               "secondary": ["Sales cycle", "Slippage", "CAC / payback", "Cost to serve", "Discount leakage", "Customer health"]},
       "B2G": {"primary": ["Contract value", "Bid pipeline", "Award rate", "Renewal / recompete", "Procurement cycle", "Contract concentration", "Margin", "Revenue at risk"], "secondary": ["Protest rate", "Compliance findings"]},
       "D2C": {"primary": ["Revenue", "Orders", "AOV", "Conversion", "CAC", "ROAS", "Repeat purchase", "Returns", "Gross margin"], "secondary": ["LTV", "Churn (subscriptions)"]},
       "B2C": {"primary": ["Revenue", "Active customers", "AOV", "Frequency", "Retention", "Gross margin"], "secondary": ["NPS", "Returns"]},
       "B2B2C": {"primary": ["Sell-in", "Sell-through", "Sell-through rate", "Partner concentration", "Partner margin", "End-consumer demand"], "secondary": ["Channel inventory", "Partner churn"]}}
kmodel = top[0] if top[0] in KPI else ("B2C" if top[0] in ("C2C", "C2B") else "B2G" if top[0] in ("G2C", "G2G") else "B2B")
profile = {"contract": "business_context_profile", "version": "1.0",
  "business_model": {"value": model, "confidence": conf, "evidence": ev[top[0]][:12] + structural, "scores": scores},
  "industry": {"seller_industry": ind, "sub_industry": sub, "confidence": ind_conf, "evidence": {"offerings": offerings},
               "customer_industries": cust_mix, "note": "Customer industries describe who the business sells to, not what the business is."},
  "business_scale": {"value": scale, "confidence": max(0.3, min(0.9, scale_conf)), "dimensions": dims,
                     "caveat": "Dataset may be a sample of accounts; revenue is a floor, not the total. No employee count."},
  "geography": regions, "revenue_model": revenue_model, "customer_model": "Organizations (named accounts, tiered)" if kmodel == "B2B" else "Individuals",
  "sales_motion": sales_motion, "distribution_model": "Direct" if not scores["B2B2C"] else "Direct + partner",
  "regulatory_context": sorted(set(cust_mix)) and ["Customer-side regulation relevant (e.g. Financial Services, Healthcare, Pharma customers)"] if any(k in cust_mix for k in ["Financial Services", "Healthcare", "Pharma"]) else [],
  "kpi_framework": {"model": kmodel, **KPI[kmodel]},
  "market_benchmark_framework": f"{ind} — {sub}; peers: enterprise IT services and software vendors",
  "needs_clarification": conf < a.min_confidence, "questions": []}
if conf < a.min_confidence:
    profile["questions"] = ["Who pays you: organizations, government bodies, or individual consumers?",
                            "Do customers buy through contracts with renewals, or per transaction?",
                            "Do partners or resellers sit between you and the end customer?"]
if not rev is None and scale_conf < 0.6:
    profile["questions"].append("Is this dataset all of your customers or a sample? Roughly how large is the company (revenue, employees)?")
print(json.dumps(profile, indent=2, default=str))
if a.out:
    json.dump(profile, open(a.out, "w"), indent=2, default=str)
