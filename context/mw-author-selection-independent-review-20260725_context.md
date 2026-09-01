# Task Context: mw-author-selection-independent-review-20260725

Created: 2026-07-25 03:30:01
Objective: 独立审阅医学作者选择或确认状态机的一致性、PICOS与翻译旧状态迁移、跨项目隔离、当前UI和审批中心行为，仅输出P0/P1/P2审阅报告，不改生产源码或运行态SQLite，不重启5174/8911
Task type: `code_open_audit`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `/Users/smkzw/.codex/AGENTS.md`
- `context/mw-author-selection-confirmation-20260725_context.md`
- `reviews/mw_author_selection_confirmation_worker_20260725.md`
- 用户指定的 contracts、PICOS、writing-reference、frontend 与直接测试文件
- 当前文件系统；5174/8911 仅作只读健康与构建检查

## Scope

- In scope: 功能、科学语义、状态机、旧状态迁移、并发、失效、审计、跨项目隔离、UI 可达性、审批中心待办、测试假阳性
- Out of scope: 安全/后门审计、生产源码修改、运行态 SQLite 修改、5174/8911 重启

## Success Criteria

- 结论写入 `reviews/mw_author_selection_confirmation_independent_review_20260725.md`
- 按 P0/P1/P2 给出可定位、可复现、可执行的独立结论
- 明确已正确路径、测试局限和剩余运行态验收
- 不改变生产源码、运行数据库或当前服务进程

## Risk Boundaries

- 只允许写本任务的 `context/`、`reviews/`、`metrics/` 记录。
- 不向生产 SQLite 写入；所有状态探针使用临时数据库。
- 不重启、不停止 5174/8911。
- 本任务由 Codex 直接独立审阅，无外部 Agent 结论替代。

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-25 03:30:01: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-25: 读取全局/项目指令、任务上下文、worker 报告及指定源码和直接测试。
- 2026-07-25: 在隔离运行目录执行 12 个聚焦模块，共 206 项测试通过。
- 2026-07-25: 使用临时 SQLite 复现 PICOS handoff 重复主键、旧 approved 未准入、来源失效后仍计确认、旧 revision 处置假成功；跨项目探针未观察到穿透。
- 2026-07-25: 只读检查 5174/8911，确认前端期望 backend build 与当前 backend build 不一致；未重启服务。
- 2026-07-25: 独立报告完成，结论为 0 P0、6 P1、2 P2，不建议放行。
