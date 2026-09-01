# Task Context: monitoring_p10_close_legacy_run

Created: 2026-07-30 08:12:11
Objective: 关闭医学监查 Checklist 空态旧风险旁路，仅允许正式 daily-run 启动门，完成前端测试与构建
Task type: `finite_code_task`
Risk: `high`
Selected agent route: `codebuddy-cli` / `hy3` / `max` (08:30 前日间替代路由)

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `/Users/smkzw/.codex/AGENTS.md`
- `AGENTS.md`
- `context/monitoring_p10_rule_release_chain_gap_audit_20260730.md`
- `frontend/src/App.jsx`
- `frontend/src/features/medical-monitoring/MedicalMonitoringDailyRunPanel.jsx`
- `frontend/src/features/medical-monitoring/MedicalMonitoringBatchPanel.jsx`
- `frontend/src/features/medical-monitoring/medicalMonitoringApi.mjs`
- `services/api/app/monitoring_daily_run_router.py`
- `services/api/app/monitoring_daily_run_service.py`
- 本轮对应测试文件与实际测试输出。

## Scope

- In scope: 关闭 Checklist 空态旧 `/modules/medical-monitoring/runs` 入口；新增正式
  daily-run 启动条件只读投影；前端仅在正式门满足时允许 prepare。
- Out of scope: 规则编译、方案准备、字段画像、医学写作、运行数据库、真实 run、
  规则发布产品链的其他 P0/P1 缺口。

## Success Criteria

- 前端源码及 API client 不再包含旧风险 run 命令。
- 空态只进入批次准备/正式 daily-run 工作区。
- 正式启动前校验当前已激活 mapping、冻结 capability snapshot、已发布规则包和产品 AI。
- readiness GET 不产生 run；POST prepare 同样执行门控。
- 医学监查前端全部测试、Vite build、daily-run 后端相邻回归通过。

## Risk Boundaries

- 不启动 API 或真实 run，不写运行数据库。
- 不修改医学写作、规则编译、方案准备、字段画像。
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-30 08:12:11: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-30: 因 00:00-08:30 禁止 aishuo，审阅路由替换为
  CodeBuddy CLI / hy3；实现由 Codex 在主工作区按授权完成。
