# Task Context: medical_monitoring_clinical_consumer_hash_shape_revalidation_20260805

Created: 2026-08-05 07:31:25
Objective: Harden the read-only clinical consumer handoff boundary so persisted event, scope, and handoff digests are strict lowercase SHA-256 values and fail closed on padded or non-string hashes, with focused source-only tests and evidence.
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_clinical_consumer_handoff.py`
- `tests/test_monitoring_clinical_consumer_handoff.py`
- Upstream hash contracts in `monitoring_clinical_event_contract.py` and
  `monitoring_clinical_projection_contract.py`.
- Current active goal and release gate records under
  `records/active_slices/medical_monitoring_goal_p10_20260730/` and
  `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/`.

## Scope

- In scope: strict lowercase SHA-256 shape validation at the read-only
  clinical consumer handoff boundary; canonical declared handoff hash
  verification; focused regression tests and source-only evidence records.
- Out of scope: clinical inference, source parsing, runtime activation,
  provider/browser/API calls, real projects, frontend redesign, and unrelated
  medical-writing implementation.

## Success Criteria

- Timeline and safety-metric event hashes, handoff scope hash, and declared
  handoff hash reject missing, non-string, padded, uppercase, and malformed
  values without normalizing them.
- Existing canonical handoff round-trip, conservation, and event-hash binding
  tests remain green.
- Focused and adjacent non-real tests pass; compile-only validation passes;
  runtime ports remain unused; no real-loop or provider evidence is created.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- The authoritative real-loop gate is read-only/blocked; keep 8911 and all
  related services, browser sessions, provider calls, and real project data
  stopped.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 07:31:25: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05 07:32-07:35: Added strict consumer digest-shape validation and
  focused rejection tests. Focused handoff **14 passed**; clinical
  event/projection plus adapter/onboarding adjacency **53 passed**; non-real
  P9 consumer/protection composite **121 passed, 17 warnings**. Compileall
  passed, Ruff unavailable, reserved ports empty, preflight and review-gate
  passed. No provider/runtime/browser/real-project action occurred.
