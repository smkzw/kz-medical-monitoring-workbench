# Task Context: mw_section_interaction_routing_20260717

Created: 2026-07-17 05:26:31
Objective: 建立当前中文M11节点交互注册表的真实运行时路由，使结构化事实、专用编辑器、表格和AI候选按节点语义进入同一写作工作台，并先完成最高价值节点的可验证闭环
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `packages/contracts/workbench_contracts/models.py`: StudyDefinition、ProtocolDocument、工作副本与请求合同。
- `services/api/app/medical_writing_authoring_journey.py`: 两阶段反问、影响预检、StudyDefinition版本与失效依赖。
- `services/api/app/medical_writing_greenfield.py`: 方案基线创建与中文M11节点投影。
- `services/api/app/medical_writing_repository.py`: 工作副本、医学批准、不可变批准快照与导出组装。
- `services/api/app/sqlite_runtime_store.py`: 运行态事务和审计持久化。
- `services/api/app/main.py`: 稳定API组合与门禁入口。
- `records/active_slices/medical_writing_m11_template_upgrade_20260717/TASK_RECORD.md`: 当前160节点模板与稳定运行边界。

## Scope

- In scope: 先建立StudyDefinition到方案文档的持久化绑定、动态一致性状态、陈旧批准/终稿导出门禁和可审计的选择性重绑定，再开放最高价值M11节点的结构化交互入口。
- In scope: 保留既有工作副本文本和不可变历史；仅重置受影响章节的当前批准状态。
- Out of scope: 自动改写用户已批准文本、静默更新稳定项目、删除旧批准快照、跨SQLite伪装为单库原子事务。

## Success Criteria

- 新建绿地文档永久保存创建时的StudyDefinition id/revision/hash，旧文档明确标为未绑定而非伪造绑定。
- StudyDefinition变化后，API和前端可明确显示陈旧状态、变更字段、受影响下游和受影响章节。
- 陈旧文档不得新增医学批准或导出医学批准终稿；草稿预览可继续但必须显式标明状态。
- 用户确认重绑定时，仅受影响章节当前批准被重置，内容和不可变历史保留，并形成可恢复、可审计记录。
- 一致性闭环通过后，至少一个结构化节点编辑器能从章节目录进入、保存、重载并影响DOCX输出。
- 至少两个真实项目完成API、浏览器、审批、DOCX和回归验证，稳定项目数据不得被测试修改。

## Risk Boundaries

- 不在稳定项目上替用户执行重绑定或批准；真实项目验收使用隔离SQLite副本。
- 不删除或改写旧批准快照、修订线程、工作副本文本和审计事件。
- 不在一致性状态未知或陈旧时开放看似成功的医学批准与正式终稿导出。
- 本切片是一条连续跨状态事务链，由Codex直接执行；超过两个独立执行包时才使用Execution Module，存在需要观点对抗的语义争议时才开Conference。

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-17 05:26:31: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-17: 重读全局`/Users/smkzw/.codex/AGENTS.md`；确认当前使用Codex直接路由，不新建Codex SubAgent。
- 2026-07-17: 发现创建时校验StudyDefinition后未把绑定持久化到ProtocolDocument，且`invalidated_dependents`没有批准/导出消费者；决定先闭合一致性链路，再做节点交互路由。
- 2026-07-17 06:34: 章节交互、一致性重绑定、双项目审批/DOCX/浏览器闭环完成；446项回归通过。视觉复核否决过加载态截图并增加四重加载门后重跑通过；稳定端口和稳定SQLite保持不变。
