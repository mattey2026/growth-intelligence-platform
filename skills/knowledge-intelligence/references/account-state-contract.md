# `account_state` Contract v2.0 (Customer Digital Twin snapshot)

v2.0 extends v1.0 (which is still accepted) with the full twin facets. It replaces the separate `account_360` and `account_health` outputs.

```json
{
  "contract": "account_state", "version": "2.0", "account_id": "", "as_of": "YYYY-MM-DD",
  "parent_account_id": null,
  "sources": [{"system": "", "status": "connected|blocked|absent", "as_of": "", "match_confidence": 0.0}],
  "company": {"name": "", "industry": "", "region": "", "business_units": [], "priorities": [{"text": "", "source": ""}]},
  "metrics": {"arr": 0, "revenue_ttm": 0, "gross_margin_pct": null, "cost_to_serve": null, "open_pipeline": 0,
              "weighted_pipeline": 0, "products_owned": 0, "utilization_pct": null, "open_sev12_cases": 0,
              "sla_breaches_90d": 0, "dso": null, "disputes_open": 0, "nps": null, "marketing_engagement": null,
              "exec_engagement_90d": 0, "days_to_renewal": null, "health_label": ""},
  "products": [{"offering": "", "arr": 0, "utilization_pct": null, "contract_end": ""}],
  "contracts": [{"id": "", "value": 0, "end": "", "notice_days": 0, "key_clauses": []}],
  "opportunities": [{"id": "", "stage": "", "value": 0, "close_date": "", "slip_p": null}],
  "stakeholders": [{"name": "", "title": "", "role": "", "strength": 0, "stance": "unknown", "owner": "", "last_contact": ""}],
  "competitors": [{"name": "", "presence": "observed|confirmed", "scope": "", "source": ""}],
  "swot": {"strengths": [{"id": "S1", "statement": "", "confidence": "", "evidence": []}], "weaknesses": [], "opportunities": [], "threats": []},
  "risks": {"revenue": {"level": "low", "signals": []}, "relationship": {}, "competitive": {}, "service": {},
            "contract": {}, "financial": {}, "stakeholder": {}, "delivery": {}, "strategic": {}},
  "predictions": [{"name": "renewal|churn|expansion|revenue_at_risk|...", "probability": 0.0, "band": [0, 0], "confidence": "", "horizon": "", "source_skill": ""}],
  "opportunities_discovered": [{"id": "", "type": "", "expected_value": 0, "status": "hypothesis|evidenced"}],
  "signals": [{"signal": "", "direction": "", "date": "", "function": "", "source": "", "evidence": ""}],
  "actions": [{"id": "", "status": "open|done|late|blocked", "owner": ""}]
}
```

**Rules.** Keep IDs stable across snapshots. Never back-date. Stakeholder stance and risks are internal-only. Store only what the user is entitled to see.
