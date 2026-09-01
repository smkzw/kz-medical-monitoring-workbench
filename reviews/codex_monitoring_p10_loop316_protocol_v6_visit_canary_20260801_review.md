# Codex Review: monitoring_p10_loop316_protocol_v6_visit_canary_20260801

Date: 2026-08-01
Delegated-agent output: `runs/codex-subagent_monitoring_p10_loop316_protocol_v6_visit_canary_20260801.md`

## Verdict

**Canary failed closed; v6 is rejected for retry or reuse.**

The job correctly persisted zero candidates. Independent review confirmed a real
provider topic/atomicity failure plus incomplete deterministic visit-boundary
coverage. RUX protocol remains NO-GO and MY009 remains blocked.

## Boundary Check

- Exactly one v6 visit POST and one attempt occurred; no repeat, retry, other-topic
  start, candidate decision, or partial salvage occurred.
- The existing native Luna session was reused once for read-only review. It did not
  mutate any file/database/service/API/candidate state; parent Codex persisted the
  returned handoff.
- The review used the App-native Codex child route; no Hermes dispatch or CLI
  compatibility fallback was used.
- 8911 was stopped immediately after terminal capture; 8911/5174 remain stopped.

## Codex Verification

- Terminal job `monai_93160e1e698569730d331fa50f6e`, attempt
  `monattempt_a4d6ee94c29040fc97fb740963f2fce6`, failed /
  `invalid_ai_output`, one initial plus one controlled repair, zero candidates.
- Response SHA-256:
  `b6939be6675b5cdb1686e12332a1bd540fbd9d142e0254808b0262901b1b22ac`.
- Codex focused monitoring suite:
  **254 passed**, 0 failed.
- Five-file adjacent medical-writing suite:
  **200 passed**, 0 failed.
- No product source changed during the canary/review slice.

## Delegated-Agent Output Review

- All five repaired candidates pass structural closure but are unsafe:
  C1/C2 combine schedule and rescheduling and retain first-dose IP administration;
  C3/C4 retain withdrawal/safety/collection or mixed visit families; C5 is an
  IP-administration clause with zero valid visit families.
- `_VISIT_TOPIC_MEDICATION_ACTION_RE` misses first-dose/administration forms. This
  implementation gap masks the clinically more specific boundary failure.
- Current family classification is also noisy because it scans review-only
  uncertainty/user actions; a single controlled repair receives only the
  response-level first error rather than complete candidate-indexed diagnostics.
- v6 fixed the old v5 list-identity and conflict-injection mechanics; those were not
  the cause of this failure.

## Residual Risk

- Provider-visible instructions and validation diagnostics must change, so the next
  offline correction requires prompt v7.
- Regex-only topic gates need field-aware negative fixtures and false-positive
  controls.
- No v7 runtime/provider behavior has been tested. Failed v6 prose remains
  unaccepted and cannot seed later candidates.
