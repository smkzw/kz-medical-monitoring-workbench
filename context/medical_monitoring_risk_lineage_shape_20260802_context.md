# Task Context: medical_monitoring_risk_lineage_shape_20260802

Created: 2026-08-02 17:42:16
Objective: 将风险Checklist来源谱系字段的非字符串形状异常从静默缺失中区分出来，保留现有只读风险消费边界并完成离线验证
Task type: `code_scoped_patch_plan`
Risk: `medium`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

风险 Checklist 已能显示来源绑定状态，但 `riskEvidenceLineageSummary` 对 `sourceRevision/sourceVersion/sourceBatch` 的非字符串值只返回空字符串，用户看到的是“缺少来源绑定”，无法区分真实缺失与字段形状异常。本轮补充与 Subject/Profile locator guard 一致的只读提示。

## Source Of Truth

- `frontend/src/features/medical-monitoring/medicalMonitoringModels.mjs`
- `frontend/src/features/medical-monitoring/medicalMonitoringModels.test.mjs`
- `frontend/src/features/medical-monitoring/MedicalMonitoringRiskChecklist.jsx`（只读确认消费路径）
- `frontend/AGENTS.md`、工作区 `AGENTS.md`、当前 release audit/coverage 与 B6/C14 gate

## Scope

- In scope: lineage token 形状状态、异常行计数、Checklist 既有状态 message、模型断言、离线回归和恢复记录。
- Out of scope: 风险事实/严重度/处置、API/backend、SQLite、权限、App/styles、B6/C13/C14、aggregate/CAS、source-token、服务、browser、真实项目和医学写作。

## Success Criteria

- 非字符串 lineage token 不得静默等同于缺失；`riskEvidenceLineageSummary` 输出 `malformedBindingRows` 并将状态保持为非 bound。
- Checklist message 明确“来源绑定字段形状异常”，仍保留不能据此判断完整或无风险的边界。
- 合法字符串、批次-only、缺失和混合版本行为不回归；Node、Python、Vite、release-gate 与 review-gate 通过。

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-02 17:42:16: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-02: 复核风险 Checklist lineage contract，确认非字符串 token 静默降为空；补充 `explicitLineageTokenState`、malformed 行计数与 fail-closed message。
- 2026-08-02: 模型 **67 passed**、医学监查 Node **22/22**、前端合同 **64 passed**、Vite **1925 modules**、release-gate **7 passed**。
