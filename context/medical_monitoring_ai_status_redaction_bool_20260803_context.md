# Task Context: medical_monitoring_ai_status_redaction_bool_20260803

Created: 2026-08-03 10:36:47
Objective: Harden only monitoring AI status override and read-only context redaction boolean boundaries with focused regressions; keep providers, browser, services, real projects and B6/C14 paths stopped.
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Workbench source under `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench`.
- Primary modules: `services/api/app/monitoring_raw_intake.py` and
  `services/api/app/monitoring_ai_service.py`.
- Primary tests: `tests/test_monitoring_raw_project_intake.py` and
  `tests/test_monitoring_ai_service.py`, followed by the full monitoring suite.
- Current P10 ledger and B6/C14 gate artifacts remain authoritative; B6 is
  `pending_review` and C14 is `blocked_pending_b6_review`.

## Scope

- In scope: strict runtime type validation for the raw-intake
  `ai_provider_configured` override and the AI read-only context
  `values_redacted` field; direct boolean consumers and focused synthetic
  regressions.
- Out of scope: provider calls, API login, service/browser starts, real project
  data, AI model routing changes, credentials, database/schema work, frontend,
  B6 reviewer outcomes, CAS/source-token activation and medical conclusions.

## Success Criteria

- String/number truthy values cannot mark the external AI override configured or
  alter the redaction contract; malformed input fails closed with a clear
  `ValueError`.
- Existing actual boolean behavior and all existing raw-intake/AI tests remain
  green; full monitoring regression passes.
- Ruff check and compile pass; no formatter churn in large historical files.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- Do not call any provider or construct a real-project AI request. Synthetic
  temporary files and fake providers in existing tests are allowed only for
  deterministic contract checks.
- No B6 outcome may be created or inferred; all authority flags remain false.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-03 10:36:47: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-03: Added strict Boolean validation for the raw-intake provider
  override and AI read-only context redaction flag; added two synthetic
  malformed-value regressions.
- 2026-08-03: Focused 2 passed; raw-intake/AI-service files **439 passed**, 18
  warnings; full `tests/test_monitoring*.py` **1809 passed**, 25 warnings in
  479.03s. Ruff check and compile passed; format baseline was preserved.
- 2026-08-03: B6 remains `pending_review`, C14 remains
  `blocked_pending_b6_review`; 8911/5174 have no listeners. No provider,
  browser, API login, service, CAS/SQLite project operation or real-project
  data was used.
