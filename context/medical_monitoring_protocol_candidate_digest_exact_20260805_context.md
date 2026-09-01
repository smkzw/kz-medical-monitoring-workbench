# Task Context: medical_monitoring_protocol_candidate_digest_exact_20260805

Created: 2026-08-05 10:08:59
Objective: Reject non-canonical protocol candidate input and frozen evidence digests without normalization
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_protocol_preparation_service.py`,
  `_frozen_candidate_context()` and `_validate_frozen_candidate_evidence()`.
- `tests/test_monitoring_protocol_preparation.py` plus the protocol rule/API,
  listing-precheck and review-boundary adjacency tests.
- `context/medical_monitoring_p9_source_only_checkpoint_20260805.md` and
  `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json`
  for the active P9 boundary and blocked P10 gate.

## Scope

- In scope: fail closed on padded/uppercase/non-string persisted or supplied
  protocol candidate input revision and frozen evidence content digests; keep
  source revision text compatibility behavior; add focused negative regressions
  and run protocol adjacency/compile checks.
- Out of scope: protocol interpretation, provider/runtime/browser/API login/
  real-project activity, authentication, schema migration, medical-writing
  data, B6/C14 review, release activation and clinical/commercial claims.

## Success Criteria

- A padded expected input digest cannot be stripped into a valid candidate
  lineage; a malformed frozen evidence content digest cannot be lowercased into
  a valid source binding.
- Existing valid candidate decisions, protocol facts and review boundaries stay
  green; focused/adjacent tests, compileall and review-gate pass.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- This is a source/evidence identity guard; it does not establish that the
  candidate's clinical interpretation is correct or medically approved.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 10:08:59: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05 10:09: Source audit found protocol candidate lineage still used
  `str(...).strip().lower()` for the expected input digest and lowercased frozen
  evidence `source_content_sha256` before comparison.
- 2026-08-05 10:10: Added exact lowercase 64-hex checks and four new negative
  regressions (one padded expected input and three frozen evidence shapes).
  The focused digest/lineage subset, including existing lineage behavior, was
  **5 passed**; the full preparation suite was **49 passed**;
  protocol adjacency: **121 passed** in 3.98s; compileall passed; Ruff
  unavailable. No runtime, service, port, browser, provider or real project
  was started.

## Source digests at checkpoint

- `services/api/app/monitoring_protocol_preparation_service.py`:
  `1f631d229482109c86d0f9e886bb91443d2e6c09bebd18426d6daa25c801f9fe`
- `tests/test_monitoring_protocol_preparation.py`:
  `b89053219266ae5944c59f5288ab30da975320ccd0619d6ddfeb8b65ba4cc34f`
