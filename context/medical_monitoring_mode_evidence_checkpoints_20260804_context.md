# Task Context: medical_monitoring_mode_evidence_checkpoints_20260804

Created: 2026-08-04 21:54:27
Objective: Require mode-specific checkpoint evidence in the offline three-mode medical-monitoring coverage contract without changing runtime execution or authority.
Task type: `finite_code_task`
Risk: `medium`
Selected agent route: `opencode-go` / `deepseek-v4-flash` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_real_loop_mode_coverage.py` — the existing
  read-only three-mode acceptance contract.
- `tests/test_monitoring_real_loop_mode_coverage.py` — its deterministic
  fixture and regression contract.
- Existing mode IDs remain frozen: `daily_incremental`, `pre_lock_total`, and
  `post_lock_fixed_total`.

## Scope

- In scope: declare immutable semantic checkpoints for each mode; require a
  mode evidence row to carry all of its checkpoints; serialize the checkpoint
  IDs; add negative/positive tests.
- Out of scope: real-loop execution, provider/browser/Playwright, API login,
  source data, risk results, medical/UAT/release authority, SQLite, or any
  product runtime state.

## Success Criteria

- Generic evidence references cannot satisfy a mode row without its complete
  mode-specific checkpoint set.
- Checkpoints from another mode are rejected at shape validation.
- Existing blocked/no-evidence mode coverage remains blocked and the
  read-only/authority flags remain unchanged.
- Focused acceptance/readiness tests, py_compile and review-gate pass.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Evidence Boundary

- This is an additive offline evidence-shape contract. The existing schema
  version remains compatible because no previously accepted mode row exists;
  the current persisted mode report has zero evidence rows and remains
  blocked.
- No runtime, service, provider, browser, SQLite or real project was started
  or read.

## Loop Log

- 2026-08-04 21:54:27: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04 21:55–21:58: Added per-mode checkpoints and strict validation;
  updated fixtures and negative tests.
- 2026-08-04 21:58: Mode coverage/acceptance/readiness contracts **57 passed**;
  py_compile passed. No runtime or provider activity occurred.
