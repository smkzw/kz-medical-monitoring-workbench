# Codex Review: monitoring_p10_protocol_v9_cutover_direct_tests_20260801

Date: 2026-08-01
Delegated-agent output: `runs/pi_monitoring_p10_protocol_v9_cutover_direct_tests_20260801.md`

## Verdict

**PASS for the offline v8→v9 durable-cutover slice.** This does not authorize
runtime startup, provider execution, canary, real-project work, release or
candidate decisions.

## Boundary Check

- Pi edited only the four authorized product/test paths in its follow-up. Its
  read-only inspection exceeded the original narrow read list; no unlisted
  product file was modified.
- Codex made two bounded repository/test corrections after broader API and Luna
  feedback. No runtime DB, medical-writing source, frontend source or real
  project was modified.
- Ports 8911/5174 remained stopped. No slice-owned process remains.

## Codex Verification

- Final hashes are recorded in the task context and pause checkpoint.
- Compile: passed.
- Repository/protocol/API: `83 passed`.
- Shared monitoring contract: `439 passed`.
- Full monitoring (one known unrelated collection blocker ignored):
  `1410 passed, 4291 deselected, 27 warnings`.
- Adjacent medical-writing sample: `98 passed, 2 failed`; both failures are
  concurrent chapter-projection expectation drift and outside this slice.
- Luna round 4 independently found no P0-P4 in-scope blocker.

## Delegated-Agent Output Review

- Pi correctly reproduced both original retry escapes and implemented the
  durable marker, exact production-key and fail-loud coverage.
- Codex rejected an over-broad already-stale interpretation after an API
  regression, preserving verified input-only compatibility.
- Luna round 3 correctly identified missing behavioral migration; the final
  transaction backfills all three old codes and retains a defensive retry gate.

## Residual Risk

- Provider-only stable job identity includes `provider`, while the SQLite unique
  tuple omits it. Luna classifies this as a separate P2; it does not affect the
  v8→v9 prompt cutover but must be fixed before provider-only rotation.
- Startup ordering, runtime contents, provider behavior and a fresh v9 canary
  remain unverified and require a separate phase.
- Parallel medical-writing drift remains owned by that lane.
