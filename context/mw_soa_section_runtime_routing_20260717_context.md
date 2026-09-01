# Task Context: mw_soa_section_runtime_routing_20260717

Created: 2026-07-17 06:36:40
Objective: 把中文M11研究流程表节点直接连接到现有SoA领域设计器、工作副本和DOCX，支持已有表格打开或受控创建，并用D001与PNH两个真实项目完成逐按钮浏览器和Word闭环
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected execution route: Codex chief architect; Kimi Code / k3 and Grok Build / grok-4.5 jointly execute and cross-QC this frontend/interaction slice.

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/medical_writing_protocol_template.py`: M11 1.3 与 `schedule_of_activities_editor`。
- `frontend/src/App.jsx`: 当前章节路由、工作副本、模板实例化与表格焦点。
- `frontend/src/features/medical-writing/StructuredTableDesigner.jsx`: SoA 领域设计器。
- `services/api/app/medical_writing_table_templates.py`: `schedule_of_activities` 模板。
- `packages/contracts/workbench_contracts/models.py`: StructuredTable 与 ScheduleOfActivitiesDefinition。
- `records/active_slices/medical_writing_soa_builder_20260713/TASK_RECORD.md`: 既有设计和真实方案证据。
- D001 与 PNH 原始方案路径按项目 manifest 和本切片 TASK_RECORD 固定。

## Scope

- In scope: 1.3 节专用入口、已有/多表选择、受控模板创建、工作副本保存重载、模块化附注、D001/PNH 隔离浏览器与 DOCX。
- Out of scope: 第二套 SoA 数据模型、静默 AI 确认、修改原始 DOCX、写稳定项目、自由画布流程图、其他文档类型。

## Success Criteria

- 从目录选中 1.3 后可直接进入真实 SoA 表格对象。
- 有表打开、无表受控创建、多表显式选择；不得静默重复。
- 附注、访视、活动与计划状态保存、重载和 DOCX 一致。
- D001/PNH 两真实项目通过隔离逐按钮与原图视觉验收，稳定库不变。

## Risk Boundaries

- 写入型 QC 只使用临时运行目录/稳定库备份，不操作稳定项目。
- 原始方案只读；原始表只能建立待确认映射，不能自动医学确认。
- 工作副本、审批、一致性和重复模板门保持失败关闭。
- Codex 保留浏览器、DOCX、临床边界和最终验收权。

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Execution Governance Added On Resume

- Codex defines the global plan, contracts, architecture, source boundaries,
  integration decision and final acceptance; it does not duplicate the bounded
  implementation assigned below.
- Because this is a frontend interaction and visual workflow, Kimi Code / k3
  and Grok Build / grok-4.5 must jointly inspect the implementation, research
  mature table-editor and ambiguous-target selection patterns where useful,
  agree the task decomposition and technical route, implement inside the
  explicit write set, and cross-QC before Codex review.
- If a build problem appears, both execution members and Codex must search
  current official documentation or mature reference implementations rather
  than relying only on recalled patterns. Web findings must be recorded as
  evidence with links and access dates; model recommendations remain
  non-authoritative until Codex verifies them.
- Do not route this slice to Codex SubAgents. Do not silently substitute a
  different model without recording provider failure and the fallback decision.

## Loop Log

- 2026-07-17 06:36:40: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-17 06:38: 完成只读审计，确认断点位于章节路由而非 SoA 底层引擎。
- 2026-07-17 06:42: 用户明确要求无损暂停；停止产品修改。本切片无产品代码写入，恢复点为先写失败合同。
- 2026-07-17 08:30: 用户恢复任务并新增执行模块治理。已重新读取全局与项目 AGENTS、Goal 和暂停记录；稳定 5174/8911 健康。当前切片改由 Kimi Code/k3 与 Grok Build/grok-4.5 共同执行和交叉 QC，Codex 保留总架构与最终验收权。
