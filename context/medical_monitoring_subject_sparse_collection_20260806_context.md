# Task Context: medical_monitoring_subject_sparse_collection_20260806

Created: 2026-08-06 00:37:29
Objective: 补齐医学监查 Timeline/Profile 对稀疏受试者集合的 fail-closed 归一化与逐域降级边界，不伪造临床数据并保持运行时门禁关闭
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `docs/medical_monitoring_manual/医学监查子系统_PRD审阅与差距矩阵.md` P1-06：稀疏受试者数据必须返回完整空结构，前端逐域降级，不伪造数据。
- `frontend/src/App.jsx` `buildSubjectView` 的画像未载入回退对象及其兼容消费面。
- `frontend/src/features/medical-monitoring/MedicalMonitoringSubjectViews.jsx` Timeline/Profile 空态与风险/事件集合消费。
- `frontend/src/features/medical-monitoring/medicalMonitoringSubjectModels.mjs` 的画像来源 lineage 空态语义。
- `tests/test_frontend_timeline_contract.py`、`frontend/src/features/medical-monitoring/medicalMonitoringSubjectModels.test.mjs` 及当前 Node/静态契约/build 证据。
- 当前 `CURRENT_REAL_LOOP_GATE_AUDIT.json`：真实 LOOP 仍 `read_only / blocked`；本轮只做离线源/UI 修复。

## Scope

- In scope: 把画像未载入回退对象的 Timeline/相关集合改为真实空集合；增加显式未载入原因；在 Subject Timeline、Patient Profile 及兼容旧画像入口中区分“未载入”与“无记录/无风险”；补充静态和 Node 回归。
- Out of scope: API/backend/SQLite/source registry/clinical facts/risk status/disposition/provider/runtime/browser/Playwright/real projects/B6/C14/medical-writing source and any production activation.

## Success Criteria

- 未载入画像不再注入可被时间线消费的占位事件；`timeline`、疗效、安全性、实验室、Query、提示和复核集合均保持完整空结构。
- Timeline/Profile 的未载入状态明确说明不能据此判断无风险；真实已载入但无记录的空态保持原有克制文案。
- 兼容旧画像入口不因空数组崩溃，且不把占位文本当作临床事件。
- 聚焦/相邻静态契约、医学监查 Node 套件、Vite 构建、医学写作保护样本和 review-gate 可复现通过；端口和真实运行门禁保持关闭。

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-06 00:37:29: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-06 00:38–00:42: Reconciled the P1-06 boundary. `buildSubjectView` now
  returns an empty Timeline collection plus an explicit unavailable reason instead
  of a placeholder event. The legacy compatibility Timeline surfaces render that
  reason as an empty state. The project-bound Timeline/Profile surfaces now keep
  unloaded profile, empty domain, malformed shape and true records distinct; an
  unloaded profile cannot be read as “no risk”, “no PD/Query” or “no events”.
- 2026-08-06 00:43: Added sparse-profile model and frontend-contract regressions.
  Focused Subject model and adjacent frontend/monitoring contracts passed **165**;
  the full medical-monitoring Node suite passed **35/35** files. Vite build passed
  with **1,957 modules transformed**; the existing >500 kB main-bundle advisory
  remains.
- 2026-08-06 00:43: The medical-writing protection sample remained **197 passed / 2
  existing translation-batch contract failures** in the untouched translation-batch
  component (`setSelectedAnchors([...payload.anchor_filter])` assertions). No
  medical-writing source was edited.
- 2026-08-06 00:44: Current real-loop gate recheck remains `read_only / blocked` with
  all authority booleans false; listeners 8911/5174/8910/4173 are empty. No
  service, browser, provider, API login, real project, runtime write, B6/C14
  action, source-token/CAS replay or release activation occurred.
