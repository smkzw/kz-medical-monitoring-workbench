# Codex Review: monitoring_p10_loop316_protocol_v5_visit_canary_20260801

Date: 2026-08-01
Delegated-agent output: `runs/codex-subagent_monitoring_p10_loop316_protocol_v5_visit_canary_20260801.md`

## Verdict

**Canary failed closed; v5 is rejected for reuse or retry.**

The runtime correctly persisted zero candidates, but the canary exposed both an
unstable list-identity defect and genuine provider topic/atomicity overaggregation.
The protocol gate and MY009 remain blocked.

## Boundary Check

- Before POST, no v5 visit job existed. Exactly one POST for
  `visit_window_and_order` created
  `monai_5e1ed560631e7e0d6be5a948571a`; no other v5 topic was started and no v4
  attempt changed.
- No candidate accept/reject/adopt/confirm/activate decision was made.
- One initial provider output plus one controlled repair occurred inside attempt 1;
  there was no job retry or repeat POST.
- 8911 was stopped after terminal evidence capture; 5174 remained stopped.

## Codex Verification

- Terminal job: failed / `invalid_ai_output` / non-retryable / zero candidates.
- Attempt `monattempt_8f67d5f58b534b33b946fbb3699df33e`;
  request 178,414 bytes; response 28,294 bytes; response SHA-256
  `8bd02c480ac4deec97e84bcef7110e42e1997741717081ded39e0f353c799e97`.
- First deterministic runtime failure:
  `protocol structural repair cannot union list items across lists`.
- Codex reused the existing native Luna reviewer session read-only. The independent
  report reconstructed all five candidates against the immutable attempt and frozen
  packet and supplied 14 required negative tests.

## Delegated-Agent Output Review

- None of the five candidate objects is safe to persist or salvage.
- `parent_match_source_ids` is causal expansion lineage, not physical-list identity;
  adjacent paragraphs 1169-1172 received sliding parent sets and were falsely split.
- PROMIS paragraph 486 was also falsely eligible as a title; PK title 1402 and item
  1405 could not bind under exact parent-set grouping.
- Independently, candidates mixed visit windows with IP stop/restart,
  dispensing/return/adherence/PK, early withdrawal, safety follow-up, AE/CM
  collection, or multiple visit action families.
- The visit packet also carried an out-of-topic IP-stop conflict, structurally
  incentivizing an invalid visit candidate.

## Residual Risk

- The original DOCX rendering was not reopened; the review used immutable quotes,
  locators and packet structure.
- No v5 repair lineage was persisted because validation failed before candidate
  persistence.
- A new provider-visible packet/repair/prompt identity was required; v5 must never be
  retried or reused.
