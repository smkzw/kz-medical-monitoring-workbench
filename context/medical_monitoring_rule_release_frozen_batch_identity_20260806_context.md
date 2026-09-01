# Task Context: medical_monitoring_rule_release_frozen_batch_identity_20260806

Created: 2026-08-06 08:00:02
Objective: 离线审计规则发布面板的冻结批次选择身份，保留重复批次可见但禁止歧义批次进入影子检查动作；不启动运行时
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/frontend/src/features/medical-monitoring/medicalMonitoringRuleRelease.mjs`
- `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/frontend/src/features/medical-monitoring/MedicalMonitoringRuleReleasePanel.jsx`
- `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/frontend/src/features/medical-monitoring/medicalMonitoringRuleRelease.test.mjs`
- `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/frontend/src/features/medical-monitoring/medicalMonitoringBatchView.mjs`
- `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/tests/test_frontend_monitoring_contract.py`
- Current read-only/blocked real-loop gate: `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json`.

## Scope

- In scope: audit and repair the frozen-batch selector inside Rule Release; preserve duplicate frozen rows with display identity, disable ambiguous rows and prevent an ambiguous batch from enabling the shadow action.
- Out of scope: batch/source/API/schema repair, shadow execution, rule publication, risk/clinical semantics, provider/browser/runtime, real projects, SQLite/CAS/B6/C14/P8 and medical-writing paths.

## Success Criteria

- Frozen batch rows retain source order and collision-safe display keys.
- Duplicate or otherwise ambiguous batch identities remain visible and disabled; automatic selection and `canRunShadow` accept only one ready row.
- Focused/full Node and Python contracts plus Vite build pass; runtime ports remain stopped.

## Risk Boundaries

- Only feature-owned offline source/tests and task records may change; no runtime or data-store write.
- Do not start 8911, 5174, 8910, or 4173; no provider, browser/API login, real project, or shadow execution.
- Display identity is UI-only and must not substitute `batch_id`, alter batch state, or authorize a shadow run.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-06 08:00:02: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-06 08:00:xx: Confirmed `frozenShadowBatches` dropped normalized batch display identity and the selector used `key={batch.batchId}`; duplicate frozen IDs could remain selectable.
- 2026-08-06 08:01:xx: Added source-indexed `displayKey`/identity metadata, unique-ready fallback selection, disabled ambiguous options, and a `selectedBatchReady` shadow-action guard. No API payload or batch source identity changed.
- 2026-08-06 08:02:25: Rule-release Node 71 passed; focused Python 95 passed; all 38 monitoring Node files passed; Vite build passed (1956 modules, existing >500 kB advisory); ports had no listeners.
