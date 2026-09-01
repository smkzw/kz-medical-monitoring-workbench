# Codex Review: medical_monitoring_my008_identity_20260805

Date: 2026-08-05
Delegated-agent output: direct Codex route; no delegated agent.

## Verdict

Pass for the declared source-integrity repair. The prior real MY008 protocol
regression is fixed without weakening lineage validation. This is not runtime
activation, P10 completion, clinical acceptance, or commercial readiness.

## Boundary check

- Product change is limited to three repository validation call sites and one
  hardening regression test.
- The validator still runs with the same arguments and raises the same errors;
  only a top-level copy is supplied so it cannot mutate a revision-bearing
  rule object.
- No API/provider/runtime/browser/Playwright route, real project execution,
  medical-writing surface, or gate evidence was changed.

## Evidence reviewed

1. Reproduced failure before editing and traced the mismatch to legacy `unit`
   versus persisted `unit_literal`; the rebuilt and stored objects differed
   only in `rule_revision_id`.
2. New deterministic hardening test proves a legacy-unit rule survives
   `store_rule_pack` and `rule_pack` with the same id and source payload.
3. Real MY008 V3/V4 selective rereview passes.
4. Full monitoring sweep passes: **2536 passed, 25 warnings**.

## Reviewer findings

- Integrity repair is coherent: repository validation no longer changes the
  object whose identity was already computed.
- The change is intentionally narrower than modifying
  `validate_rule_field_lineage`; callers that require normalized lineage still
  receive the function's return value or pass an explicit copy.
- The test covers the exact failure mode rather than only checking that a
  generic lifecycle operation completes.

## Residual risk

- `ruff` was unavailable, so lint is unverified in this runtime.
- Browser/runtime/independent-AI/three-study scientific acceptance remains
  unverified because the authoritative gate is still read-only/blocked.
- The metric candidate contract from LOOP 5.318 remains source-only and is not
  yet reachable through a read-only API/UI review surface.

## Hermes review-gate

This was direct Codex source work; no external provider or delegated agent was
used. The verification file under
`records/active_slices/medical_monitoring_my008_identity_20260805/` is the
evidence source for the review gate.
