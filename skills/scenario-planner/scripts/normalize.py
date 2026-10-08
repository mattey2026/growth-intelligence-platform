#!/usr/bin/env python3
"""
normalize.py: map any source table (CRM export, spreadsheet, warehouse extract)
onto the canonical semantic model, for opportunities and accounts.

USAGE
  python normalize.py input.csv|xlsx --entity opportunity [--sheet S] [--map mapping.json] \\
         [--stage-map stages.json] [--out canonical.csv]

- Proposes a column → canonical field mapping, with a confidence score per mapping.
- --map overrides the proposal with a mapping the user has confirmed: {"Deal Value": "amount", ...}
- --stage-map maps the source's stage labels to the canonical ladder index (1–6);
  otherwise a keyword guess is made and flagged for the user to confirm.
- Adds lineage columns (source_file, source_row).
- Entities: opportunity, account, contact, case, invoice, subscription, product,
  project, vendor, employee.
- Writes mapping_report.json next to the output. Unmapped required fields are
  listed, never invented.
"""
import argparse, difflib, json, re, os
import pandas as pd

SYN = {
    "opportunity": {
        "opportunity_id": ["id", "opportunity id", "opp id", "deal id", "opportunity number", "record id"],
        "account_id": ["account id", "accountid", "company id", "customer id", "customer no", "account"],
        "account_name": ["account name", "company", "company name", "customer", "client"],
        "opportunity_name": ["opportunity name", "deal name", "name", "opportunity"],
        "amount": ["amount", "deal value", "value", "acv", "tcv", "est revenue", "estimated revenue", "total"],
        "currency": ["currency", "currencyisocode", "currency code"],
        "stage": ["stage", "stagename", "deal stage", "sales stage", "pipeline stage", "status"],
        "close_date": ["close date", "closedate", "expected close", "est close", "estimated close date", "close"],
        "forecast_category": ["forecast category", "forecastcategoryname", "forecast", "commit"],
        "owner_id": ["owner", "owner id", "deal owner", "rep", "sales rep", "ae"],
        "created_date": ["created date", "createddate", "create date", "created"],
        "outcome": ["outcome", "result", "won/lost", "is won", "iswon"]},
    "account": {
        "account_id": ["id", "account id", "company id", "customer id", "customer no"],
        "account_name": ["name", "account name", "company", "customer", "client"],
        "industry": ["industry", "sector", "vertical"],
        "country": ["country", "region", "billing country"],
        "annual_revenue": ["annual revenue", "revenue", "turnover"],
        "employees": ["employees", "employee count", "headcount", "size"],
        "owner_id": ["owner", "account owner", "rep"]},
    "contact": {
        "contact_id": ["id", "contact id", "person id"], "full_name": ["name", "full name", "contact name", "contact"],
        "email": ["email", "email address", "e mail"], "title": ["title", "job title", "designation", "role"],
        "account_id": ["account id", "company id", "customer id", "account", "company"], "phone": ["phone", "mobile"]},
    "case": {
        "case_id": ["id", "case id", "ticket id", "incident id", "case number", "ticket number", "number"],
        "account_id": ["account id", "account", "customer", "company", "caller company"],
        "priority": ["priority", "severity", "sev", "urgency"], "status": ["status", "state"],
        "opened_date": ["opened", "created", "created date", "opened at", "open date"],
        "closed_date": ["closed", "closed date", "resolved", "resolved at", "closed at"],
        "category": ["category", "type", "subcategory", "issue type"], "subject": ["subject", "short description", "title"]},
    "invoice": {
        "invoice_id": ["id", "invoice id", "invoice number", "document number", "bill number"],
        "account_id": ["account id", "customer id", "customer no", "customer", "bill to"],
        "amount": ["amount", "invoice amount", "total", "gross amount", "net amount"],
        "invoice_date": ["invoice date", "date", "posting date", "bill date"], "due_date": ["due date", "net due date"],
        "paid_date": ["paid date", "payment date", "cleared date"], "status": ["status", "payment status"],
        "currency": ["currency", "currency code"]},
    "subscription": {
        "subscription_id": ["id", "subscription id", "contract id", "agreement id"],
        "account_id": ["account id", "customer id", "customer", "account"], "product": ["product", "plan", "sku"],
        "arr": ["arr", "annual value", "annual recurring revenue", "acv"], "mrr": ["mrr", "monthly value"],
        "start_date": ["start date", "start", "effective date"], "end_date": ["end date", "renewal date", "expiry", "end"],
        "quantity": ["quantity", "seats", "licenses", "licences", "units"]},
    "product": {
        "product_id": ["id", "product id", "sku", "material", "item id"], "product_name": ["name", "product name", "product", "description"],
        "family": ["family", "category", "product family", "line"], "list_price": ["list price", "price", "unit price"]},
    "project": {
        "project_id": ["id", "project id", "project number"], "project_name": ["name", "project name", "project"],
        "account_id": ["account id", "customer", "client"], "status": ["status", "rag", "health"],
        "start_date": ["start date", "start"], "end_date": ["end date", "go live", "finish"], "budget": ["budget", "value", "contract value"]},
    "vendor": {
        "vendor_id": ["id", "vendor id", "supplier id", "vendor number"], "vendor_name": ["name", "vendor name", "supplier", "vendor"],
        "category": ["category", "spend category"], "spend": ["spend", "annual spend", "amount"]},
    "employee": {
        "employee_id": ["id", "employee id", "worker id", "user id"], "full_name": ["name", "full name", "employee", "worker"],
        "role": ["role", "job title", "title", "position"], "manager_id": ["manager", "manager id", "reports to"],
        "region": ["region", "territory", "location"], "start_date": ["start date", "hire date", "joining date"],
        "quota": ["quota", "target"]},
}
REQUIRED = {"opportunity": ["opportunity_id", "amount", "stage", "close_date"], "account": ["account_id", "account_name"],
            "contact": ["full_name"], "case": ["case_id", "opened_date"], "invoice": ["invoice_id", "amount", "invoice_date"],
            "subscription": ["subscription_id", "end_date"], "product": ["product_name"], "project": ["project_id"],
            "vendor": ["vendor_name"], "employee": ["employee_id"]}
LADDER = [(1, ["prospect", "qualif", "lead", "new"]), (2, ["discover", "needs", "analysis"]),
          (3, ["solution", "demo", "evaluat", "value"]), (4, ["proposal", "quote", "price"]),
          (5, ["negotiat", "contract", "legal", "commit", "verbal"]), (6, ["closed", "won", "lost"])]


def clean(s):
    return re.sub(r"[^a-z0-9/ ]", " ", str(s).lower()).strip()


def propose(cols, entity):
    """Map source columns to canonical fields: exact synonym matches first, then fuzzy (>= 0.75)."""
    out, used = {}, set()
    for field, syns in SYN[entity].items():  # pass 1: exact matches
        for c in cols:
            if c not in used and clean(c) in syns:
                out[c] = {"field": field, "confidence": 1.0}
                used.add(c)
                break
    mapped = {v["field"] for v in out.values()}
    for field, syns in SYN[entity].items():  # pass 2: fuzzy matches for remaining fields
        if field in mapped:
            continue
        best, score = None, 0.0
        for c in cols:
            if c in used:
                continue
            s = max(difflib.SequenceMatcher(None, clean(c), x).ratio() for x in syns)
            if s > score:
                best, score = c, s
        if best is not None and score >= 0.75:
            out[best] = {"field": field, "confidence": round(score, 2)}
            used.add(best)
    return out


def detect_dayfirst(series):
    """Return (dayfirst, basis). Day-first if any a/b/yyyy value has a > 12; month-first if any b > 12."""
    s = series.dropna().astype(str)
    parts = s.str.extract(r"^(\d{1,2})[/.-](\d{1,2})[/.-]\d{2,4}")
    if parts.dropna().empty:
        return False, "not slash-formatted"
    a_, b_ = parts[0].dropna().astype(int), parts[1].dropna().astype(int)
    if (a_ > 12).any():
        return True, "day-first (a value has day > 12)"
    if (b_ > 12).any():
        return False, "month-first (a value has day > 12 in second position)"
    return None, "AMBIGUOUS — every value could be either day-first or month-first; confirm with --dayfirst"


def stage_index(label, smap):
    if smap and label in smap:
        return smap[label], "user"
    l = str(label).lower()
    for idx, keys in LADDER:
        if any(k in l for k in keys):
            return idx, "guess"
    return None, "unmapped"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--entity", choices=list(SYN), default="opportunity")
    ap.add_argument("--sheet")
    ap.add_argument("--map")
    ap.add_argument("--stage-map")
    ap.add_argument("--out", default="canonical.csv")
    ap.add_argument("--dayfirst", choices=["yes", "no"], help="override date-order detection")
    a = ap.parse_args()
    df = pd.read_excel(a.file, sheet_name=a.sheet or 0) if a.file.lower().endswith((".xlsx", ".xls", ".xlsm")) else pd.read_csv(a.file)
    prop = propose(list(df.columns), a.entity)
    if a.map:
        user = json.load(open(a.map))
        prop = {k: {"field": v, "confidence": 1.0, "source": "user"} for k, v in user.items()}
    ren = {k: v["field"] for k, v in prop.items()}
    out = df.rename(columns=ren)[list(ren.values())].copy()
    out["source_file"] = os.path.basename(a.file)
    out["source_row"] = range(2, len(out) + 2)  # spreadsheet row numbers (header is row 1)
    report = {"entity": a.entity, "mapping": prop,
              "unmapped_source_columns": [c for c in df.columns if c not in prop],
              "missing_required": [f for f in REQUIRED[a.entity] if f not in out.columns],
              "low_confidence": [k for k, v in prop.items() if v["confidence"] < 0.9]}
    if a.entity == "opportunity" and "stage" in out.columns:
        smap = json.load(open(a.stage_map)) if a.stage_map else None
        res = out["stage"].map(lambda x: stage_index(x, smap))
        out["stage_index"] = res.map(lambda r: r[0])
        report["stage_mapping"] = {str(s): {"index": stage_index(s, smap)[0], "basis": stage_index(s, smap)[1]}
                                   for s in out["stage"].dropna().unique()}
        # Derive outcome from stage text when no outcome column exists.
        if "outcome" not in out.columns:
            st = out["stage"].astype(str).str.lower()
            out["outcome"] = st.map(lambda s: "won" if "won" in s else ("lost" if "lost" in s else "open"))
            report["outcome_derived_from_stage"] = True
    report["date_order"] = {}
    for dcol in [c for c in out.columns if c.endswith("_date")]:
        if dcol in out.columns and not pd.api.types.is_datetime64_any_dtype(out[dcol]):
            if a.dayfirst:
                df_, basis = a.dayfirst == "yes", "user override"
            else:
                df_, basis = detect_dayfirst(out[dcol])
            report["date_order"][dcol] = basis
            if df_ is None:
                report.setdefault("blocking_questions", []).append(f"{dcol}: date order ambiguous; rerun with --dayfirst yes|no")
                df_ = False
            out[dcol] = pd.to_datetime(out[dcol], errors="coerce", dayfirst=df_, format="mixed")
    for money in [c for c in ["amount", "arr", "mrr", "list_price", "budget", "spend", "quota"] if c in out.columns]:
        out[money] = pd.to_numeric(out[money].astype(str).str.replace(r"[,$€£₹\s]", "", regex=True), errors="coerce")
    out.to_csv(a.out, index=False)
    json.dump(report, open(os.path.splitext(a.out)[0] + "_mapping_report.json", "w"), indent=2, default=str)
    print(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":
    main()
