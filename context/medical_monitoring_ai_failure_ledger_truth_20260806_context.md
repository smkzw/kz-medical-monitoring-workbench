# Task Context: medical_monitoring_ai_failure_ledger_truth_20260806

Created: 2026-08-06 04:34:21
Objective: Keep daily independent-AI failure evidence visible and fail-closed when counts and detail disagree; add conservative failure-kind labels without retry authority
Task type: `code_scoped_patch_plan`
Risk: `medium`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Workbench source: `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench`.
- Requirements: `docs/medical_monitoring_manual/医学监查子系统说明书.md`, the active P10 trace under `records/active_slices/medical_monitoring_goal_p10_20260730/`, and `records/active_slices/medical_monitoring_independent_ai_contract_audit_20260803/`.
- Source/API contract: `services/api/app/monitoring_daily_run_ai_service.py` and `_ai_progress_dict` in `services/api/app/monitoring_daily_run_router.py`.
- UI contract: `frontend/src/features/medical-monitoring/MedicalMonitoringDailyAiEvidence.jsx`, `medicalMonitoringDailyAiEvidence.mjs`, CSS, and focused tests.
- Current gate: `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json` remains read-only/blocked; no provider/runtime/browser/real-project action is permitted.

## Scope

- In scope: strict validation that AI failure count agrees with failure detail length when both are available; display failure evidence whenever detail exists even if the count is missing/inconsistent; conservative display-only labels for known failure-code/message families (timeout, rate limit, invalid structure, low confidence, configuration/transport, stale input, cancelled/blocked, unknown).
- Out of scope: retryability decisions, retry buttons/API calls, backend schema changes, provider calls, services/ports, browser/API login, real projects, runtime/SQLite/CAS/B6/C14, P8 authority, Safety/PV, App.jsx and medical-writing/reference.

## Success Criteria

- A failure detail cannot disappear merely because its count is zero/missing; an inconsistency produces a visible partial warning and the detail remains visible.
- Failure labels are conservative classification aids only; unknown codes stay “失败原因待核对”, and no label implies retry permission or clinical meaning.
- Missing/invalid detail remains fail-closed and never becomes a zero/no-risk result.
- Focused/full frontend tests, syntax/build checks pass; all guarded ports remain stopped.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-06 04:34:21: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-06 04:35:00: Re-anchored the daily AI progress payload. The current card renders failures only under `counts.failed > 0` and does not validate `failed` against returned details; this can hide a failure row under inconsistent state. The patch will remain read-only and conservative.
