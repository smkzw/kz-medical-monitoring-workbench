# Task Context: medical_monitoring_canonical_batch_diff_20260806

Created: 2026-08-06 01:02:05
Objective: 补齐医学监查 canonical module 的项目中立批次差异只读读取契约，复用不可变 batch/source/row diff，服务器身份 fail-closed，不启动运行时
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `docs/medical_monitoring_manual/医学监查子系统_PRD审阅与差距矩阵.md` P0-03：不可变批次、项目级业务键、结构漂移、行/字段差异和风险迁移必须形成项目中立闭环。
- `services/api/app/monitoring_batch_diff.py`、`monitoring_batch_repository.py`、`monitoring_batch_service.py`：现有 immutable source/batch/row diff 实现。
- `services/api/app/medical_monitoring_router.py`：canonical module 路由、服务器身份与 source-readiness 门。
- `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json`：当前 `read_only / blocked` 运行门禁。
- `services/api/app/main.py`：生产装配点，必须只注入已存在的 batch repository/service。

## Scope

- In scope: 将 detailed immutable batch diff 接入 `/api/projects/{project_id}/modules/medical-monitoring/batch-diff`；要求服务器验证身份、`READ_SOURCE_EVIDENCE` 动作、canonical project scope、跨项目拒绝、缺失依赖 fail-closed、完整输出 hash 与字段分页。
- Out of scope: 真实文件导入、provider/AI、SQLite 迁移或批次写入、风险处置迁移、B6/C14/source-token/CAS、真实项目、浏览器/Playwright、前端重构、医学写作源文件。

## Success Criteria

- canonical route 仅消费注入的 `MonitoringBatchRepository`/`MonitoringBatchService`，不接受客户端 actor，不产生写入。
- 身份缺失或批次服务未接入时分别返回可审计的 fail-closed 错误；跨项目批次在调用 diff 前返回 404。
- 分页只裁剪 `field_changes`，保留 `field_change_total`、`output_sha256`、row/schema/removal/identity 证据。
- route/identity/batch diff/repository 聚焦回归和编译通过；既有医学写作未变更；8911/5174/8910/4173 保持停止。

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-06 01:02:05: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-06: 审计确认旧 `/monitoring/batch-diff` 是 legacy 入口；canonical module 尚未消费 batch diff。
- 2026-08-06: 新增 canonical 只读路由与 `READ_SOURCE_EVIDENCE` 身份动作，main 注入既有 batch repository/service。
- 2026-08-06: 增加身份缺失、正常分页、跨项目拒绝、依赖缺失四项路由回归；聚焦与相邻测试通过。
