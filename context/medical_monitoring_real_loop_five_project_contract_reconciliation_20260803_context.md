# Task Context: medical_monitoring_real_loop_five_project_contract_reconciliation_20260803

Created: 2026-08-03 21:54:42
Objective: Reconcile the offline medical-monitoring real-loop readiness and prompt-manifest contracts with the already frozen five-project serial acceptance matrix, without starting runtime or granting authority
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_real_loop_acceptance.py` (already frozen five-project serial acceptance set).
- `services/api/app/monitoring_real_loop_readiness.py` and `monitoring_real_loop_prompt_manifest.py` (currently stale three-project/24-row set).
- `records/active_slices/medical_monitoring_real_loop_serial_matrix_20260803/` (offline contract evidence requiring five tester routes, two roles and five candidate projects).
- User-supplied project candidate list recorded in `records/active_slices/medical_monitoring_goal_p0_20260729/REAL_PROJECT_TEST_MATRIX.md` and the existing prompt-manifest record.
- Current B6/C14/CAS/real-loop gates: remain blocked; this task must not alter them.

## Scope

- In scope: align readiness and prompt-manifest constants/docs/tests to the five acceptance project IDs; add exact project-specific prompt context for MY008-3-02 and MY008-3-01; regenerate the derived prompt audit artifact and update task-scoped evidence.
- Out of scope: source approval, project-file parsing, batch registration, provider dispatch, service/browser/runtime startup, API login, SQLite/risk/disposition writes, B6/C14/CAS/source-token changes, medical/UAT/release decisions.

## Success Criteria

- Readiness and prompt-manifest builders require exactly five project IDs: MG-K10-SAR, Ruxolitinib-AD, MY008-3-02, MY008-3-01 and MY009-UC.
- Prompt coverage is exactly 5 × 2 × 4 = 40 unique references, scenario IDs, variants, hashes and prompt texts; project identity markers remain explicit.
- Existing serial acceptance contract and readiness use the same project set; current synthetic contract fixtures remain structurally reviewable but real sources/gates remain blocked.
- Focused real-loop tests, adjacent release/gate tests, Ruff/compile checks, and no-listener checks pass. No runtime or project state is changed.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-03 21:54:42: Task initialized by `tools/hermes_workflow_guard.py init-task`.
