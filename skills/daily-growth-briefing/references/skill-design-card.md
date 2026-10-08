# Skill Design Card — daily-growth-briefing (v4.0, 24-item standard)

| Item | Detail |
|---|---|
| Skill name | daily-growth-briefing |
| Business problem | Sellers and leaders must hunt across systems for what changed; signals are missed |
| Persona | AEs, managers, CSMs, executives, RevOps |
| Trigger | Morning schedule; "what should I focus on today" |
| Inputs | User identity and role, book of accounts and deals |
| Data sources | Outputs of every monitor, plus email and calendar |
| Connectors / tools | signal_ranker; all monitors |
| Context requirements | Role, owned entities, preferences, quiet hours |
| Analytics | Change detection across monitors |
| Predictive | Inherits predictions from the source skills |
| Reasoning | Why each signal matters to this user |
| Decision logic | value × urgency × confidence × novelty × relevance |
| Recommendations | Top 3–7 actions, each with "Claude can do this" |
| Actions | Prepares the underlying actions; one-click hand-off to the owning skill |
| Approval | Each action, in the owning skill |
| Output | Daily Growth Briefing |
| Evidence | Evidence and source skill per item |
| Confidence | Carried from the source |
| Error handling | A failed monitor is listed, never hidden |
| Security | Only the user's entitled data |
| Auditability | Log of delivered signals and actions taken |
| Baseline | Time to find "what changed"; signals missed |
| Success metrics | Actions taken; lead time on risks; minutes saved |
| Test scenarios | AE morning; exec morning; no signals; failed source |
| Failure modes | Noise overload; stale signals; alert fatigue |
