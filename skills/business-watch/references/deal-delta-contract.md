# `deal_delta` Output Contract (v1.0)

`sales-meeting-follow-through` produces this record after every processed customer conversation. The Deal Evidence Auditor, Forecast Integrity Analyst, Buying Committee Intelligence, and Deal Strategy skills consume it. Keep field names and enums stable; add fields only in a new minor version.

```json
{
  "contract": "deal_delta",
  "version": "1.0",
  "meeting": {
    "id": "string (calendar or transcript id)",
    "date": "ISO 8601",
    "source_type": "transcript | notes | voice_memo",
    "attendees": [{"name": "string", "email": "string|null", "side": "buyer|seller|partner|unknown", "title": "string|null"}]
  },
  "account_id": "string",
  "opportunity_id": "string|null",
  "match_confidence": "high|medium|low",
  "facts": [
    {
      "category": "pain|metric|budget|timeline|decision_process|decision_criteria|paper_process|economic_buyer|champion|competition|risk|other",
      "statement": "string (plain summary)",
      "speaker": "string",
      "speaker_side": "buyer|seller",
      "evidence": {"quote": "string (<= 25 words)", "timestamp": "hh:mm:ss|null"},
      "confidence": "high|medium|low"
    }
  ],
  "commitments": [
    {"owner": "string", "owner_side": "buyer|seller", "action": "string", "due": "ISO date|null", "evidence": {"quote": "string", "timestamp": "string|null"}}
  ],
  "stakeholders_new_or_changed": [
    {"name": "string", "title": "string|null", "inferred_role": "economic_buyer|technical_evaluator|user|legal|procurement|champion|influencer|unknown", "basis": "string"}
  ],
  "crm_reconciliation": [
    {"field": "string", "crm_value": "any", "evidenced_value": "any", "status": "confirm|update|new|contradiction", "evidence": {"quote": "string", "timestamp": "string|null"}}
  ],
  "risk_flags": [{"type": "string", "severity": "high|medium|low", "evidence": "string"}],
  "approval": {"status": "pending|approved|partial|rejected", "approved_by": "string|null", "approved_at": "ISO 8601|null"}
}
```

**Consumer rules**
- Treat only `approval.status` of `approved` or `partial` as confirmed by the seller. Pending records are evidence, not confirmed fact.
- Always prefer `speaker_side: buyer` facts over seller statements when scoring buyer commitment.
