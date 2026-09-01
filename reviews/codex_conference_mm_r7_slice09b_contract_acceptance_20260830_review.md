# Codex Conference Review: mm_r7_slice09b_contract_acceptance_20260830

Date: 2026-08-30

## Verdict

`ACCEPT_R7_SLICE_09B_CONTRACT_V0_2`

P0=0, P1=0, P2=0, P3=0, P4=0. v0.1 与 v0.2 合并冻结为 `FROZEN_R7_SLICE_09B_SCHEMA_MIGRATION_CONTRACT_V0_2`，解锁 synthetic/offline governed implementation；不接受 09B 实现、Slice-09、R7、R8、真实项目或生产完成。

## Boundary Compliance

- 会商仅阅读合同、三项执行证据、09A 合同/实现和 R1/R7 当前 schema 源码。
- 未修改产品源码、前端或医学写作，未启动 8911/5174、模型、浏览器或真实项目。
- 两轮均使用同一 session `01a05136-008a-7000-b015-9928f6ad0ea7`，路由 `pi/cms-router/minimax-m3:xhigh`，与执行路由 `openai-codex/gpt-5.6-luna` 独立；无 fallback。
- guard/runner 生成 Hermes-compatible 会商包；Hermes 未作为 Pi/cms-router 的传输层。

## Round 1 Findings And Remediation

第一轮识别 6 个 P0 和若干 P1：普通 constructor 可绕过只读检查、launch open/upgrade 耦合、staging 位置、崩溃恢复入口、limited 数据展示、后端写阻断深度、恢复点漂移、WAL/member set 和 fixture 复用等。

Codex 将全部 P0 与关键 P1 写入 v0.2，同时纠正第一轮把 staging 建议放在 live 项目目录内部的问题：staging/rollback 必须是同 runtime root 下的 sibling；否则第一次目录替换会把 staging 一起移动。

## Round 2 Independent Result

第二轮在同一 session 完整读取 v0.2，并逐条对账第一轮 A1–I2：

- 普通 constructor current-only；只读 inspector 优先，legacy 仅 staging migration。
- exact schema manifest 管理无 marker 的 risk/control。
- R1 marker 3、future marker、损坏/不完整项目分别有准确中文结果。
- `dataCoverage=limited`、`supportCode` 和医学写作字段不进入合同。
- 只读由持久化层只读 facade 与 mutable constructor fail-closed 共同保证。
- 恢复点漂移同键冲突，callback 校验 expected state。
- sibling staging、`st_dev`、WAL/SHM、09A member/fingerprint/artifact helper 复用均冻结。
- 三个崩溃恢复入口、step digest、进度冻结和 requiresReopen 均冻结。

第二轮结论为 P0=P1=P2=P3=P4=0。N1–N3 仅是 implementation hygiene：启动扫描并发、只读 facade 禁用字段 lint、完成后 staging 清理策略；不构成合同缺陷，也不扩大本切片。

## Main-Venue Codex Decision

Codex 接受第二轮归零结论。v0.1 继续作为基础，v0.2 为优先补充；实现必须以合并合同为权威，不得采用 worker 报告中的冲突分支。合同之外不新增未来 schema、真实项目迁移、复杂页面、医学写作耦合或自动历史清理。

## Final Decision

冻结 R7 Slice-09B 合同 v0.2，下一步连续进入 governed implementation：先实现只读 schema inspector/manifest 与 synthetic legacy fixtures，再实现 migration plan/ledger/state machine、R1 4/5→6、launch v1/v2/v3→v4、产品中文 DTO 与写阻断，最后完成故障注入、确定性、全量及相邻回归和独立实现会商。
