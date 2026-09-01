# Task Context: medical_monitoring_r1_controller_binding_20260809

Created: 2026-08-09 23:38:15
Objective: 在隔离 R1 POC 中建立应用自有 controller，将 capability attempt 生命周期与 manifest work unit 的预注册、运行绑定、结果持久化、终态推进和崩溃后幂等对账闭环，不启动服务或真实项目
Task type: `code_open_audit`
Risk: `medium`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md` 中的真实进度、内部术语不外露、AI 不直接晋升医学事实等设计合同。
- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md` 的 R1 应用 controller 闭环要求。
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/capability_runtime.py` 的 provider-neutral attempt 与不可变 journal 合同。
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/store.py` 的 manifest work-unit ledger、capability binding、candidate-only persistence 和审计链。
- 当前文件系统及 synthetic/offline 测试是本切片的最终事实。

## Scope

- In scope:
  - 调用前持久化 attempt → manifest work unit 不可变分配；
  - runtime 在 journal claim/replay 后、transport 前通知应用 controller；
  - 真实 running 绑定、终态原始/候选证据持久化后的 work-unit 推进；
  - 中文、可读的正在/完成/未完成/暂停进度语句；
  - 进程中断后对未调度、已终态未持久化、已中断 attempt 的幂等对账；
  - synthetic/offline 聚焦、相邻和 R1 核心回归。
- Out of scope:
  - UI/浏览器、后台服务、8911 端口、真实 provider/endpoint/项目；
  - 并行开发中的医学写作子系统与产品运行码；
  - R2+、临床风险规则扩展、多模型调度策略和真实数据。

## Success Criteria

- transport 开始前，分配已持久且 work unit 是真实 running；无 journal/claim 不得伪造 running。
- work unit 仅在 `persist_capability_attempt` 成功后才能 passed/failed；全程不产生 canonical facts。
- transport 无响应体时仍封存有界的失败证据，不留下无证据终态。
- 崩溃窗口（预注册后未调度、journal 终态后未持久化）重启后可用原 request 幂等恢复，已终态 attempt 不重复 transport。
- 分配冲突、profile 不一致、内容重哈希篡改和过时 manifest 均 fail closed。
- 聚焦测试、capability/authoritative progress 相邻回归、R1 核心回归、Ruff、compileall 通过；独立审阅者拥有最终验收权。

## Risk Boundaries

- 只修改隔离 R1 POC 及其 context/review/metrics/evidence；不修改医学写作和产品运行码。
- 不启动服务、8911、浏览器、真实模型或真实项目。
- controller 不选择 provider/model，不持有密钥，不跳过 capability journal，不使用通用 work-unit API 伪造 AI 进度。
- AI 输出始终 candidate-only；工作项 passed 只表示该分析单元执行完成，不表示医学结论已确认。
- 审阅者不改代码；Codex 仅在独立审阅接受和决定性检查通过后收口。

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.
- A provider catalog/auth/transport preflight is diagnostic, not a live capability verdict: timeout, auth refresh failure, or malformed probe output must be recorded and followed by one real route attempt. Only a missing executable or explicit invalid/retired/unlisted model may stop before that attempt.

## Loop Log

- 2026-08-09 23:38:15: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-10: 完成现有 runtime/store 合同检查，确认应用层缺少 claim 后、transport 前的生命周期桥接。
- 2026-08-10: 选择“不可变预注册分配 + runtime observer + Store 现有权威 ledger”，不引入第二套 scheduler/状态机。
- 2026-08-10: 新增 `controller.py` 与 synthetic/offline 测试；新增无响应体时的有界 transport 证据封存。
- 2026-08-10: controller + capability runtime + authoritative progress 相邻回归 97 passed；改动文件 Ruff 通过。
- 2026-08-10: 首轮独立 Luna VETO 指出 immutable assignment 并发 v2、declared 未 claim 绑定和 failed/blocked 后 resume 断链；完成事务内重读、claim 门与严格 continued_from 重开纠偏。
- 2026-08-10: 第二轮独立 VETO 指出 Store 终态可绕过 persistence、claimed attempt 可绕过 controller assignment；Store 现逐项验证 assignment/audit/完整 persistence footprint 并自主计算 evidence_count。
- 2026-08-10: 决定性回归为 controller+authoritative 51、四组相邻 170、R1 core 273；Ruff、compileall 通过，8911 无监听。
- 2026-08-10: 同一持久 Luna session `019fe746-ded2-7b83-9636-ff75466cacd2` 亲自复现两条旧绕过均 fail closed，排除跨 manifest resume 候选误报，最终 `ACCEPT`，P0-P4 全为 0。
- 2026-08-10: 本切片收口；下一安全动作是让隔离 synthetic UI/background shell 只读消费已接受的 audience projection，不直接读取 provider/attempt/backend 身份，不启动 8911 或真实项目。
