# Task Context: medical_monitoring_goal_p0_20260729

Created: 2026-07-29 00:35:35
Objective: 冻结医学监查当前实现、共享接口与并行文件所有权，建立真实项目测试矩阵并复用医学写作独立AI配置完成真实就绪验证，产出P0五份可执行合同并通过退出门
Task type: `code_open_audit`（原 `long_horizon_code` 初始化因路由守卫 allowlist 冲突失败，未实际分派）
Risk: `critical`
Selected agent route: `kimi-code` / `kimi-code/k3-256k` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `/Users/smkzw/Documents/康哲项目资料/AI/说明书/医学监查子系统说明书.md`
- `/Users/smkzw/Documents/康哲项目资料/AI/说明书/医学监查子系统_PRD审阅与差距矩阵.md`
- `/Users/smkzw/Documents/康哲项目资料/AI/说明书/医学监查子系统_分阶段实施与LOOP计划.md`
- 当前工作区代码、测试、真实项目原始方案和原始 listing。

## Scope

- In scope: 当前能力真值、共享接口/数据所有权、并行文件所有权、三个真实项目矩阵、独立 AI 最小真实探针。
- Out of scope: P1 以后生产功能修改；医学写作文档、编辑器、运行态和测试项目。

## Success Criteria

- P0 五份合同和任务记录落盘。
- 所有 P0 缺口具有输入、通过标准和后续阶段。
- 医学写作并行文件冻结且无覆盖。
- 产品内独立 AI 真实请求通过并具有脱敏证据。

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-29 00:35:35: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-29: `long_horizon_code` 路由被守卫拒绝；改为 Codex 直接 P0 审计，未将路由失败误判为产品阻塞。
- 2026-07-29: 独立 AI 监查语义探针通过，耗时 136442 ms。
- 2026-07-29: 集中回归 133 通过、1 个源码字符串合同失败；运行语义未发现对应回归。
