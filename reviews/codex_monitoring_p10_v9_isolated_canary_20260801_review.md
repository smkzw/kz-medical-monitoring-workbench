# Codex Review: monitoring_p10_v9_isolated_canary_20260801

Date: 2026-08-01
Direct evidence:

- `runs/execution/monitoring_p10_v9_isolated_canary_20260801/ATTEMPT1_ZERO_SUBMIT_GATE.md`
- `runs/execution/monitoring_p10_v9_isolated_canary_20260801/ATTEMPT2_TERMINAL_EVIDENCE.md`

## Verdict

**ATTEMPT 2 TERMINAL FAIL-CLOSED AFTER EXACTLY ONE POST.**

v9 is frozen as `failed/invalid_ai_output`. It is not a functional or
scientific canary pass and must never be retried, reused, salvaged or silently
reclassified.

## Boundary Check

- No product source or authoritative runtime changed during the canary.
- Only task-owned 8911 was started and then gracefully stopped.
- Exactly one POST created exactly one job and one attempt.
- 5174 stayed stopped. 18911 remained untouched.

## Codex Verification

- Attempt 1 exposed and then closed the audit-timestamp/startup dependency
  blockers without POST.
- Attempt 2 used the isolated runtime, created job
  `monai_5f66dc5d1c9c77c561a637389bc2`, and hard-waited to terminal without
  repeat submission or controller re-dispatch.
- Exactly one attempt,
  `monattempt_8a683aa19e1a4cd790339552da2612bf`, contains the initial provider
  output plus one controlled repair output; persisted candidates remain zero.
- Terminal evidence reproduced candidate 3 as mixed
  `reschedule + schedule` under v9. Subsequent independent review also found
  unsupported `补访`, source-fidelity and study-completion/end leakage.
- The isolated SQLite integrity check passed. Authoritative DB/WAL hashes
  remained frozen and 8911 was stopped immediately after capture.
- Authoritative monitoring DB/WAL hashes remained frozen.
- Tests were not run because the attempt ended at the pre-POST gate and the
  product defect requires a separate scoped corrective.

## Delegated-Agent Output Review

The controlled runtime evidence is Codex-direct. Independent scientific review
was subsequently used to interpret the provider output, not to alter the frozen
v9 run. No functional, scientific or release acceptance is claimed.

## Residual Risk

- v9 has real provider output but is terminal invalid output; it is evidence,
  not reusable work.
- The corrected behavior belongs to fresh identity v10.
- Any v10 runtime step begins with a new zero-submit isolation and authority
  gate; this review does not authorize POST.
