# Codex Review: monitoring_p10_v10_visit_semantic_corrective_20260801

Date: 2026-08-01
Delegated-agent outputs:

- `runs/pi_monitoring_p10_v10_visit_semantic_corrective_20260801.md`
- `runs/pi_monitoring_p10_v10_visit_semantic_corrective_20260801_followup.md`
- `runs/pi_monitoring_p10_v10_visit_semantic_corrective_20260801_followup2.md`

## Verdict

**PASS FOR OFFLINE v10 CORRECTIVE AND ZERO-SUBMIT PREPARATION ONLY.**

This does not authorize a provider call, POST, canary, candidate decision,
runtime migration or release.

## Boundary Check

- Product changes are limited to the service and three monitoring test files.
- The initially undeclared `tests/test_monitoring_ai_api.py` edit was reviewed
  and accepted as a necessary adjacent v10 prompt-contract assertion.
- No service, provider, port, browser, runtime DB or real project was used.
- Pi used one session, an initial pass and exactly two controlled same-session
  recovery passes; there was no fallback or re-dispatch.

## Codex Verification

- Codex reproduced the exact v9 repaired-candidate bundle and the cleaned v10
  replay, including the schedule-reference, unsupported `补访`, conflict-only
  evidence, open-label phase-premise and study-completion/end boundaries.
- Final service hash:
  `f1e7276a7d6705d258203f879ea89d677a16659f3b36ba7c56a55a2495578ff6`.
- Final direct probes:
  - `视为研究结束访视` and `视为研究终止访视` are schedule-only;
  - `视为整个试验结束`, `视为本研究终止` and equivalent determinations
    remain completion errors.
- Compile plus focused/adjacent combination:
  `674 passed, 17 warnings`.
- Final monitoring selection:
  `1468 passed, 4391 deselected, 27 warnings in 594.07s`.
  The sole excluded collection file is the unrelated parallel medical-writing
  private-symbol matrix.
- The reused Luna reviewer matched the final hash and returned no
  P0/P1/P2/P4. Its gate is PASS only for zero-submit preparation.

## Delegated-Agent Output Review

The initial Pi patch was materially incomplete; direct Codex probes and two
independent Luna challenge rounds found and closed source-fidelity, Chinese
numeric/reference, study-end-name, conflict-evidence and unsupported-premise
gaps. The two controlled follow-ups stayed within the accepted shared contract.
Codex did not accept delegated confidence as proof and independently reran the
full monitoring selection after the final one-line regex change.

## Residual Risk

- P3: `视为本研究终止` is covered by a final pure-function probe but lacks a
  separately named persisted parameter. It is not a zero-submit blocker.
- Runtime/provider behavior for v10 remains deliberately unverified.
- v9 remains a terminal invalid-output job and cannot be retried, reused,
  salvaged or silently reclassified.
- The provider-only stable-ID/SQLite uniqueness issue remains separate and is
  not expanded into this prompt-version corrective.
