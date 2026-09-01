# Task Context: mw_candidate_fact_state_trace_20260719

Created: 2026-07-19 21:57:27
Objective: 补齐医学写作AI候选从竞品证据到医学经理选用及写入工作副本的结构化事实采用与审计溯源，不增加二次审批、不改变现有候选安全边界
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `packages/contracts/workbench_contracts/models.py`
- `services/api/app/medical_writing.py`
- `services/api/app/medical_writing_repository.py`
- `services/api/app/sqlite_runtime_store.py`
- `tests/test_medical_writing_revision_api.py`
- `tests/test_medical_writing_revision_application.py`
- `tests/test_medical_writing_working_copy_persistence.py`
- Qoder PID 39908 / `Qwen3.8-Max-Preview`同一会话的只读审计报告：
  `records/qoder_full_system_audit_20260719/QODER_CANDIDATE_FACT_STATE_AUDIT.md`
- 用户已明确：医学经理点选某一候选即代表该候选已由当前医学作者采用，
  不再增加同角色的第二次“待医学批准”。

## Scope

- In scope:
  - 为每个AI修订候选保存其实际引用证据对应的来源类型集合；
  - 明确候选在医学经理点选前后是`candidate_only`还是`adopted`；
  - 在线程层保存候选来源类型并集，并把采用依据贯通接受、写入工作副本
    审计事件；
  - 以加法字段和默认值保持旧SQLite JSON记录可反序列化；
  - 覆盖竞品方案证据候选、普通当前项目修订和旧记录兼容。
- Out of scope:
  - 不改变AI提示词、候选正文或证据检索排序；
  - 不新增二次审批、质量评分硬阻断或额外用户确认；
  - 不修改前端视觉和交互；
  - 不更改数据库表结构或运行时部署。

## Success Criteria

- 竞品方案证据生成的候选在提交时明确标记为`candidate_only`，不得被表示为
  当前项目已确认事实。
- 医学经理执行`accept`后，唯一选中候选变为`adopted`，线程保存非空采用依据，
  同轮其他候选仍为未采用状态。
- `submitted`、`accept`、`applied`三个审计事件都能追溯证据来源类型和事实采用状态；
  `accept`与`applied`事件还包含采用依据。
- 旧版缺少新增字段的线程JSON仍能以安全默认值加载，无数据库迁移。
- 旧JSON规范化后执行接受动作，不会因新增默认字段触发伪造的stale-write
  冲突。
- 定向合同、API、SQLite持久化及工作副本应用测试通过，Ruff通过。

## Risk Boundaries

- 允许写入上述合同、服务和测试文件；工作区不是Git仓库，编辑前必须读取当前文件，
  不覆盖并行用户或代理变更。
- 事实采用状态只能由用户`accept`动作从`candidate_only`转为`adopted`；
  生成完成、盲审完成或写入前状态均不得自动升级。
- “采用”仅表示当前医学作者选用该候选，不等同于独立复核者批准或监管结论。
- Qoder输出仅作设计证据，Codex负责源码、测试和运行时最终验收。

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-19 21:57:27: Task initialized by `tools/hermes_workflow_guard.py init-task`.
