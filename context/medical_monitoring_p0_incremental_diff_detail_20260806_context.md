# Task Context: medical_monitoring_p0_incremental_diff_detail_20260806

Created: 2026-08-06 04:14:12
Objective: 在不解锁真实运行时、不选择P8 evidence authority的前提下，为医学监查日常增量批次差异增加可审计的只读明细与回源核对提示，保持差异不等于风险、缺失不等于零、身份阻断fail-closed。
Task type: `code_scoped_patch_plan`
Risk: `medium`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `docs/medical_monitoring_manual/医学监查子系统_PRD审阅与差距矩阵.md`：P0-03 增量批次差异、结构漂移、删除身份与可追溯性要求。
- `frontend/src/features/medical-monitoring/MedicalMonitoringDailyDiffSummary.jsx` 与 `.css`：当前运行内差异摘要。
- `frontend/src/features/medical-monitoring/medicalMonitoringDailyDiffView.mjs`：差异快照 fail-closed 归一化合同。
- `services/api/app/monitoring_batch_diff.py`、`services/api/app/monitoring_daily_run_service.py`：项目中立差异 payload 和安全阻断语义（只读核对，不启动服务）。
- `tests/test_frontend_monitoring_contract.py`、`frontend/src/features/medical-monitoring/medicalMonitoringDailyDiffView.test.mjs`：现有静态/Node 回归。
- `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json`：真实 LOOP gate 的当前阻断事实。

## Scope

- In scope: 在现有冻结 diff 摘要中增加可审计的结构/字段/身份摘要、受控样本和回源核对提示；扩展归一化单元测试与静态合同；记录验证证据。
- Out of scope: P8 evidence authority 选择或实现、B6/C14、SQLite/runtime/source-token、真实项目/真实 listing、8911/5174/8910/4173、provider/browser/Playwright/API 登录、Safety/PV、医学写作、后端算法或数据库变更。

## Success Criteria

- 结构、字段、移除身份阻断和可确认移除的状态能在桌面首屏以克制的只读方式辨识；缺失/非法 payload 仍显示“待核对”，不补零、不把差异当风险。
- 详细样本有稳定上限、明确“仅供回源定位”语义，不把 business key 或字段值冒充医学结论；不增加任何 mutation 控件或 API 调用。
- `medicalMonitoringDailyDiffView` 归一化测试覆盖合法、缺失、非法、空值和样本截断；现有医学监查静态/Node/build 回归继续通过。
- 记录真实 LOOP gate 仍 read-only/blocked，且没有启动服务、provider、浏览器或真实项目。

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- 不改变后端差异算法、风险身份持久化或 evidence authority；不增加客户端 actor/确认者字段；UI 只读。
- 任何来源定位信息仅按服务端现有 payload 展示，缺少 locator 或字段时 fail-closed。

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-06 04:14:12: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-06 04:16:00: Codex re-anchored latest AGENTS, P10 gate and current batch/diff source contracts; selected a bounded frontend-only P0-03 detail surface because the P8 authority fork remains unresolved.
- 2026-08-06 04:20:00: Added strict detail normalization and a collapsed read-only disclosure for schema/field/identity/removal/missing-domain evidence; samples are capped at 8 and never include raw values.
- 2026-08-06 04:21:00: Added malformed-detail and truncation assertions plus a static no-mutation/read-only contract.
- 2026-08-06 04:23:00: Focused Python 73 passed, all medical-monitoring Node 37/37 passed, module syntax check passed, and Vite build passed; no reserved ports were listening.
