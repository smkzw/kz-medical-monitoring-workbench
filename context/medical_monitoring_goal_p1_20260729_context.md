# Task Context: medical_monitoring_goal_p1_20260729

Created: 2026-07-29 00:53:54
Objective: 拆分医学监查前后端模块边界，建立只读模块摘要与可恢复深链合同，对共享main.py和App.jsx仅做最小挂载且不影响医学写作
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `records/active_slices/medical_monitoring_goal_p0_20260729/`
- `/Users/smkzw/Documents/康哲项目资料/AI/说明书/医学监查子系统_分阶段实施与LOOP计划.md` P1
- 当前 `services/api/app/main.py`、`frontend/src/App.jsx`、共享来源/风险/工作箱服务和消费者测试。
- React 官方 Effects 文档、MDN History API 和 React Router 官方文档仅用于路由方案比较。

## Scope

- In scope:
  - 新建医学监查后端 router/summary 模块和前端 `features/medical-monitoring` 目录。
  - 无副作用模块摘要接口。
  - `project/scope/site/subject/risk/view/batch` 深链焦点解析与 History API 同步。
  - 对 `main.py` / `App.jsx` 的最小兼容挂载。
  - 共享消费者、医学写作不受影响和浏览器深链验证。
- Out of scope:
  - P2 的新来源/批次/diff 存储。
  - P3/P4 的通用方案事实、规则和 AI 业务编排。
  - P5/P6 的风险 UI 与可视化重设计。
  - 医学写作功能文件。

## Success Criteria

- 直接打开监查、总看板进入、风险/受试者深链进入均恢复正确焦点。
- 模块摘要读取不触发风险重算或写库。
- 写作页面切换和编辑状态不受监查 URL 状态污染。
- 医学监查功能代码不再继续新增到共享根组件。
- 相关确定性测试、前端构建和真实桌面浏览器回归通过。

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-29 00:53:54: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 路由选择：当前应用尚无路由依赖。P1 使用原生 `URLSearchParams` + History API 实现兼容深链，避免在模块拆分阶段引入全应用路由迁移；保留未来迁移到成熟路由库的接口边界。
- 已完成显式监查运行命令、只读摘要/快照、URL 深链挂载以及 RUX-03-002
  真实项目浏览器验证；GET 读取前后 SQLite SHA 与行数保持不变。
- 已把医学监查纯模型和演示夹具从 `App.jsx` 迁入 feature 目录并切换真实运行时
  import。生产构建、39 项纯模型合同和 34 项前端监查合同通过。
- 当前恢复点：完成 `MedicalMonitoringSubjectViews.jsx` 与
  `medicalMonitoringSubjectModels.mjs` 新文件审阅后，由 Codex 对 `App.jsx` 做
  单写者接线并删除旧页面/专属 helper，再做真实 Timeline/Profile 深链回归。
