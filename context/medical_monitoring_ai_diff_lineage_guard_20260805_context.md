# Task Context: medical_monitoring_ai_diff_lineage_guard_20260805

Created: 2026-08-05 09:16:29
Objective: 在不启动 AI/provider/runtime 的前提下，阻断增量日常运行缺失或错绑差异快照时被当作初始基线提交独立 AI
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_daily_run_analysis_service.py` — daily-run to
  independent-AI submission boundary.
- `services/api/app/monitoring_daily_run_repository.py` — immutable run and
  diff-snapshot lineage fields.
- `services/api/app/monitoring_daily_run_ai_service.py` — initial-baseline vs
  incremental AI selection semantics.
- `tests/test_monitoring_daily_run_analysis_service.py` — focused offline
  analysis and lease-release regressions.
- `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json` — runtime/provider authority boundary.

## Scope

- In scope: require an incremental daily run to have a present diff snapshot
  bound to its exact previous baseline and algorithm version before independent
  AI submission; reject an unexpected diff on an initial baseline; add focused
  tests and evidence records.
- Out of scope: provider/runtime/browser/Playwright activation, real projects,
  B6/C14 writes or replay, frontend changes, database migrations, medical
  conclusions and the parallel medical-writing subsystem.

## Success Criteria

- Missing, wrong-baseline or wrong-algorithm diff snapshots fail before the AI
  submission step and release the worker lease.
- Existing initial-baseline and valid incremental paths retain behavior.
- Focused analysis tests, all real-loop contract tests, compile checks,
  review-gate and empty-port checks pass; authority remains unchanged.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 09:16:29: Task initialized by `tools/hermes_workflow_guard.py init-task`.
