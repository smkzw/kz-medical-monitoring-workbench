# Codex Conference Review: mm_r7_slice_05_background_recovery_contract_20260828

Date: 2026-08-28

## Verdict

**PASS AFTER REVISION — contract frozen as v0.2.**

## Boundary Compliance

Both roles were read-only, used their declared Pi/Grok routes, completed one
round without fallback, and did not start services/models/projects or touch the
frontend/medical-writing tree. Hermes was not a declared transport for this packet.

## Participant Outputs Reviewed

- Pi identified the run-level primary key, CAS heartbeat, failed-dependency
  livelock and prepare-during-run gaps.
- Grok proved that ordinary R1 work-unit completion is owner-blind, so the draft
  could not honestly promise rejection of every old-owner callback; it also
  separated ledger headline from control overlay and defined executable tests.

## Conference Panel Review

Both reports materially challenged the draft. Their common recommendations were
incorporated: one owner per run, generation CAS, snapshot reads, no auto-resume,
failed-dependency termination and no fake terminal retry.

## Main-Venue Codex Review

Codex checked R1 `background_progress`, work-unit begin/complete, capability
leases, checkpoint/recover and R7 Slice-04 sources. The frozen v0.2 explicitly
states the residual same-fingerprint delayed-complete behavior and keeps real
owner-bound model retry for Slice-06.

## Codex Independent Verification

Frozen contract exists with SHA-256
`590285e545a0d61ac9049b278e4b61cfaef8e1a22f56131a842ff7677978d65d`.
This was a contract-only pass; implementation tests and browser checks were not
run. No UI is in scope, so ego(lite) is deferred to Slice-07.

## Final Decision

Authorize a bounded Slice-05 implementation packet against v0.2. Contract
acceptance does not accept implementation, background execution or R7 overall.
