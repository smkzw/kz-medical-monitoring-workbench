# Codex Conference Review: mm_r7_slice_05_background_recovery_acceptance_20260828

Date: 2026-08-28

## Verdict

PASS — limited synthetic/offline Slice-05 acceptance after required revision.

## Boundary Compliance

Both participants were read-only. No service, model, real project, frontend,
R1/R6 source or medical-writing product source was changed. Ports 8911 and
5174 remained closed. The conference was linked to the execution packet and
excluded its Luna execution node. Hermes workflow guard and session-runner
records preserve the declared routes and same-session continuations.

## Participant Outputs Reviewed

- Pi / Gemini 3.7 Flash high: recommended conditional acceptance and correctly
  identified stale receipt evidence, but its final text retained superseded
  counts; Codex did not use those stale numbers as current proof.
- Grok Build 4.6 medium: reproduced expired-stop rollback and final-unit false
  continue, then re-reviewed the repaired bytes in the same session. Its final
  pass accepted the implementation boundary subject to a progress-recovery
  contract erratum and refreshed receipt. The generated conference context and
  main plan were initially unfilled templates; Codex completed them before the
  final gate and did not treat those templates as evidence.

## Conference Panel Review

Codex accepted the two reproduced P1 findings, fixed them, added expiry-stop-
continue, final-unit stop, progress rebuild, product stop/continue and finished
copy tests, and aligned progress leakage scans. The frozen v0.2 contract remains
byte-stable; `medical_monitoring_r7_slice_05_background_recovery_contract_errata_20260828.md`
clarifies that progress may first persist an expired lease interruption and
then read a later consistent snapshot. The five R6 failures are obsolete
cache-inclusive boundary assertions, not medical-writing source drift; R6 was
not edited.

## Main-Venue Codex Review

Codex reproduced the material state-machine failures, owned all source changes,
reran the deterministic and adjacent gates, reconciled the contract wording,
and compared the final receipt hashes to disk. Participant assertions that
still referenced older bytes or counts were excluded from the decision.

## Codex Independent Verification

Current-byte verification: focused runtime/determinism 47 passed, product 28,
full R7 125, R1 core 327, R6 functional 758 with five named legacy boundary
tests deselected, isolated compileall 70, receipt JSON valid, ports 8911/5174
`connect_ex=61`. No browser/visual check was appropriate because Slice-05 has
no frontend surface and the contract forbids starting the service.

## Final Decision

Accept the exact receipt-hashed bytes as R7 Slice-05 synthetic/offline only.
This does not accept R7 overall, real model execution, real projects, browser
UX, two-process kill-9 recovery, exactly-once delivery or Slice-06.
