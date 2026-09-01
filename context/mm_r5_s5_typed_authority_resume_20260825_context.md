# Task Context: mm_r5_s5_typed_authority_resume_20260825

Created: 2026-08-25 19:51:37
Objective: 从已冻结R5-S5 v0.4.1 REVISE暂停点恢复，设计并验证最小真实typed-source authority delta；在独立接受前不修改v0.4.1、不创建producer、不启动8911、不触碰医学写作
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md`
- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md`
- `context/medical_monitoring_r5_s5_public_authority_v0_4_1_pause_20260821.md`
- 已接受 parent、semantic、temporal v0.1/v0.2、error-replay coverage delta 的 manifest、acceptance record、schema、generator 与 verifier。
- 被拒绝的 v0.4 与当前 REVISE v0.4.1 只作为负面证据，不是权威实现。
- 当前文件系统及实际 SHA 是最终事实。

## Scope

- In scope：审计 272 个 v0.4.1 public-authority 目标叶的真实上游来源；设计最小 typed-source authority delta；冻结 constructor、identity/content-hash、selector/reducer/cardinality、deferred 语义与挑战门；完成作者验证和独立 fresh review。
- Out of scope：直接修补 v0.4.1、创建 11 个 producer/runtime/test/evidence 文件、R5 UI、产品服务、浏览器、真实项目/模型、医学写作、安全专项。

## Success Criteria

- 2026-08-25 根据 264/272 false-join 实证，废止“每个输出叶必须有第二套独立 typed 值权威”的原推定；accepted v0.2 `AuthorityBundleV02` 是唯一序列化输入权威，frozen typed record 只是无损 decoder。
- 268 个 packet-reachable 叶通过 accepted recipe 输出与 parent packet 比较闭合；4 个 shared cutoff 叶由 accepted `cutoff_binding` 确定性构造，并按 parent schema object-content-hash recipe 验证。
- 任何 second-truth-plane、recipe closure、constructor digest、upstream pin、保护边界或目标叶污染均 fail-closed。
- fresh isolated reviewer 对唯一稳定 SHA 返回精确 ACCEPT；否则保留 REVISE/STOP，不解锁 v0.4.1 或 producer。
- 8911 保持停止；医学写作 542 项保护面和既有 accepted/rejected 快照 SHA 不变。

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- 只允许为本 delta 新建明确命名的 context/review/artifact/generator/verifier 文件；不得覆盖已接受或被拒绝历史。
- 不得用目标值、expected packet、候选矩阵或自报 hash 生成所谓独立 authority。
- 不得因门禁复杂而增加新临床真值、错误码或产品功能。

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.
- A provider catalog/auth/transport preflight is diagnostic, not a live capability verdict: timeout, auth refresh failure, malformed output, or a stale/incomplete catalog must be recorded and followed by one real route attempt. Explicit user-selected routes are not blocked merely because the catalog does not list them; only a missing executable or native transport boundary may stop before that attempt.

## Loop Log

- 2026-08-25 19:51:37: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-25 19:52: 已重新读取最新规则、`ponytail`、v1.1 设计/实施计划结构与 v0.4.1 暂停记录；当前路由为 Codex direct/high。
- 2026-08-25 20:28: 依据 fresh reviewer 矛盾审阅，将 272 叶明确分为 268 recipe-to-packet 叶与 4 accepted-binding constructor 叶；不再宣称存在第二 typed 真值平面。
- 2026-08-25 20:46: 完成两轮修订、Codex 全矩阵验证和同会话 fresh reviewer 精确 ACCEPT；接受仅限 typed-authority delta v0.1 的最终 manifest，v0.4.1 与 producer 仍锁定。
- 2026-08-25 20:52: 已冻结 v0.4.2 实施契约计划，明确五个权威 registry、四项 fail-open 的主门禁攻击和精确边界；下一安全动作为在新路径实现 generator/verifier。
