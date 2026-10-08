# Skill Design Card — knowledge-intelligence (v5.0, 24-item standard)

| Item | Detail |
|---|---|
| Skill name | knowledge-intelligence |
| Business problem | Wrong or stale document versions create risk |
| Persona | Everyone; RFP, pricing, competitive skills |
| Trigger | 'Latest policy', 'which document is right' |
| Inputs | Question; repositories |
| Data sources | SharePoint, Confluence, Drive, KB, CLM |
| Connectors / tools | knowledge_catalog |
| Context requirements | Status taxonomy; stale threshold |
| Analytics | Version groups, authority rank |
| Predictive | — |
| Reasoning | Content conflict comparison |
| Decision logic | Approved > published > draft; recency |
| Recommendations | Archive, own, review |
| Actions | Governance changes via the owner |
| Approval | Any document-store change |
| Output | Answer with source |
| Evidence | Document, version, section |
| Confidence | Authority score |
| Error handling | No approved source → marked Unverified |
| Security | Repository ACLs; no cross-repository inference |
| Auditability | knowledge_answer |
| Baseline | Time to authoritative answer; wrong-version incidents |
| Success metrics | −70% time; zero wrong-version customer answers |
| Test scenarios | Pricing v3 vs v4 draft; stale security paper |
| Failure modes | Blending conflicting facts |
