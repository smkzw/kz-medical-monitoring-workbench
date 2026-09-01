# Task Context: medical_monitoring_signal_lifecycle_revalidation_20260803

Created: 2026-08-03 04:34:02
Objective: 为 signal→review→human decision→action→recheck 生命周期契约增加只读、可重放、可篡改检测的证据边界；保持诊断-only，不能授予 B6/C14、provider、runtime、write 或医学权限。
Task type: `code_open_audit`
Risk: `medium`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_signal_lifecycle_contract.py`
- `tests/test_monitoring_signal_lifecycle_contract.py`
- `records/active_slices/medical_monitoring_signal_lifecycle_contract_20260803/TASK_RECORD.md`
- Current B6/C14 and P10 ledger under `records/active_slices/medical_monitoring_goal_p10_20260730/`.
- The synthetic evidence artifact created by this task is the only persisted input for replay.
- No real project, provider, service, browser or runtime state is an authority source for this slice.

## Scope

- In scope: add a pure revalidation module/test, replay one explicitly synthetic lifecycle
  envelope, and persist a diagnostic-only evidence artifact.
- Out of scope: B6/C14 outcomes, risk-store migration, source admission, provider calls,
  API/service/browser execution, real projects, frontend, medical writing, or any authority grant.

## Success Criteria

- Reconstruct the typed signal/review/decision/action/recheck chain and compare the persisted
  lifecycle report with a deterministic replay.
- Detect artifact bytes/SHA drift, report tampering, unsafe paths and true authority flags.
- Keep evidence freshness separate from lifecycle validity and keep every authority flag false.
- Focused and adjacent tests, compile, Ruff and review-gate pass; 8911/5174 remain stopped.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- This is direct Codex work; no delegated agent, provider, browser or service is used.
- The synthetic chain is not a medical outcome and must remain labeled as such.
- Revalidation may report a blocked underlying lifecycle; it must never promote that state.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-03 04:34:02: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-03 04:35-04:40: Added pure replay/file-integrity boundary, focused tests and a
  synthetic evidence envelope; no external state or runtime was touched.
