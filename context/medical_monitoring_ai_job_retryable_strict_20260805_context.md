# Task Context: medical_monitoring_ai_job_retryable_strict_20260805

Created: 2026-08-05 00:45:38
Objective: Harden the monitoring AI job retryable contract against bool-like coercion while preserving persisted SQLite validation and offline-only scope
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_ai_contracts.py` (`MonitoringAiJob`)
- `services/api/app/monitoring_ai_repository.py` (`_sqlite_bool` and `_job`)
- `tests/test_monitoring_ai_repository.py` (persisted retryable boundary regressions)
- `tests/test_monitoring_ai_quality.py` (quality consumer fixture for `MonitoringAiJob`)
- Existing P10 ledger and completion audit under `records/active_slices/medical_monitoring_goal_p10_20260730/` and `records/active_slices/medical_monitoring_project_completion_audit_20260804/`
- Current filesystem is authoritative; this slice is source-only and must not activate runtime gates.

## Scope

- In scope: make `MonitoringAiJob.retryable` a strict boolean contract; add a direct regression for bool-like values; preserve the repository's strict SQLite `0/1` reader and all existing retry semantics; update task evidence.
- Out of scope: provider calls, service/API startup, browser/Playwright tests, real-project data, database migration, B6/C14 review or activation, medical conclusions, and unrelated medical-writing files.

## Success Criteria

- `MonitoringAiJob` accepts `True`/`False` and rejects `0`, `1`, numeric strings, and boolean strings for `retryable`.
- Existing repository persisted `0/1` behavior and malformed-value fail-closed tests remain green.
- Focused and adjacent monitoring-AI tests, compile, Ruff, and reserved-port checks pass.
- Review/metrics/record files state explicitly that this is offline source evidence only and that B6/C14 and real LOOP gates remain unchanged.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- No external model dispatch is used; Codex remains final authority.
- Do not modify runtime databases or start 8911, 5174, 8910, or 4173.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 00:45:38: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05 00:46: inspected the contract and repository; `_sqlite_bool` already fails closed for persisted values, while the Pydantic model still allows bool-like coercion. Next: strict model field plus direct regression.
- 2026-08-05 00:47: `StrictBool` and a four-case regression were added. Focused 68, adjacent 551, and decisive 970-test groups passed; compile, Ruff and reserved-port checks passed. No runtime/provider/browser/real-project action occurred.
- 2026-08-05 00:48: review and metrics prepared. Next safe action is another bounded source-only P7/P8/P9 gap; runtime remains blocked by formal B6 and source-token/CAS/identity gates.
