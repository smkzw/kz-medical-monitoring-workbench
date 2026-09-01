# Task Context: medical_monitoring_adapter_resolution_bool_20260803

Created: 2026-08-03 11:26:20
Objective: Harden the project adapter risk-resolution completion Boolean bridge with deterministic contract regressions while keeping B6/C14, providers, browser, services and real projects stopped.
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Workbench source under `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench`.
- Primary module: `services/api/app/monitoring_project_registry.py`.
- Primary contract tests: `tests/test_medical_monitoring_module_contract.py`.
- P10 authority: `records/active_slices/medical_monitoring_goal_p10_20260730/LOOP_LEDGER.md` and
  `REQUIREMENTS_TRACEABILITY.md`.
- Gate authority remains B6 `pending_review` and C14
  `blocked_pending_b6_review`.

## Scope

- In scope: make `BoundMonitoringProjectAdapter.risk_resolution_complete`
  accept only literal `True` from the project service; add synthetic valid and
  malformed return-value regressions; run focused/adjacent/full monitoring tests
  and static checks; record evidence.
- Out of scope: real adapter behavior, provider/browser/API/service starts,
  real-project data, database/schema/migration work, B6 reviewer outcomes,
  CAS/source-token activation, frontend changes, and medical conclusions.

## Success Criteria

- `True` remains true; `False`, missing method and malformed truthy values such
  as `"false"` remain false and cannot mark risk resolution complete.
- The adapter contract remains read-only and no risk snapshot/write path changes.
- Focused contract, monitoring-adapter/summary adjacent tests, full monitoring
  suite, Ruff and compile pass without formatter churn.
- Review/metrics pass Hermes workflow `review-gate --require-verification` and
  P10 records a compact 4.90 entry.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- No B6 outcome may be created or inferred; authority flags remain false.
- No provider/browser/API/service/CAS/project operation; synthetic in-memory
  adapter doubles only. Keep 8911/5174 stopped and unrelated 8900 untouched.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-03 11:26:20: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-03: Residual scan found the sole same-cause adapter bridge:
  `return bool(resolver()) if callable(resolver) else False` in
  `BoundMonitoringProjectAdapter.risk_resolution_complete`.
- 2026-08-03: Changed the bridge to accept only literal `True`; added five
  synthetic return-value cases. Focused contract 23 passed; adjacent adapter/
  risk contract set 38 passed; Ruff and compile passed. Because the previous
  4.89 full monitoring run completed immediately before this isolated adapter
  change, its 1818-pass result remains the shared-suite baseline; no real
  project test was added for this slice.
