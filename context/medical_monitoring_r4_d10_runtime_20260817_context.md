# Task Context: medical_monitoring_r4_d10_runtime_20260817

Created: 2026-08-17 21:32:51
Objective: 在 R4 POC 内实现并独立验收冻结 D10 v0.6 与已接受 312-case artifact 的 synthetic/offline 项目及跨中心聚合 runtime，保持 8911 停止并保护医学写作、真实项目与 R5/UI
Task type: `long_horizon_code`
Risk: `high`
Selected agent route: `opencode-go` / `deepseek-v4-flash` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- 冻结 D10 v0.6 合同：`reviews/medical_monitoring_r4_d10_project_signal_slice_contract_v0_6_20260816.md`，SHA-256 `c613bb7cad82caa6fa477ee2dd28bfca48b805b73503c646401a0aa237deff95`。
- 当前已接受 D10 artifact authority 修订链与 Worker-01 精确 SHA：`context/medical_monitoring_r4_d10_authority_correction_worker01_acceptance_20260818.md`。原 `context/medical_monitoring_r4_d10_artifact_freeze_acceptance_record_20260817.md` 仅为历史证据，其旧 accepted-source-membership 结论已被显式取代。
- 只读 D10 authority/catalog/oracle/registry/quota 与三个 generator、独立 verifier、artifact tests；runtime 禁止 import/read oracle、registry、quota、generator、verifier 或测试。
- 已独立接受的 D09 runtime 结构：`src/mm_r4/d09_contracts.py`、`d09_evaluator.py`、`d09_projection.py` 及 D09 runtime/closure tests，仅作工程结构与反过拟合参考，不覆盖 D10 语义。
- 当前文件系统是最终事实；冻结合同、artifact 与外部 verifier raw-SHA anchor 不得修改。

## Scope

- In scope：仅在 `poc/medical_monitoring_ai_native_r4` 内新增 D10 synthetic/offline runtime 与测试。
- Work item 1：D10 immutable typed contracts、test-only artifact adapter、deterministic evaluator、stable/evaluation identity、global/L0/L1 gate、measure/origin/comparability/change/cutoff/R2-domain facts与 312-case exact disposition/core/trace/source parity。
- Work item 2：renderer-neutral 项目投影、中文原生 audience text、风险标记、hotspot、跨中心/历时 count surface、完整 Query、visibility/deep-link、R2 handoff 及 authoritative rebuild validator。
- Work item 3：公共导出、mutation/reorder/replay/anti-overfit/static closure、emitted-object tamper、focused/adjacent/full R4 回归与独立验收。
- Allowed Worker-01 writes：`src/mm_r4/d10_contracts.py`、`src/mm_r4/d10_adapter.py`、`src/mm_r4/d10_evaluator.py`、`tests/test_d10_adapter.py`、`tests/test_d10_runtime_contract.py`。本轮不得修改 `__init__.py`、D01-D09 或 artifact。
- Out of scope：R5/UI、8911/服务、真实项目/患者数据、真实模型端点、产品路径、医学写作子系统，以及系统安全设计/测试。

## Success Criteria

- Runtime 语义只从 accepted typed facts 与冻结 authority/method/policy 计算，不读取或分支于 `case_id`、fixture/test id、`mutation_context`、mutation class、oracle/registry/quota、`SYN-*` 字串、自由文本描述或合成 revision-hash 约定。
- Worker 01 至少形成可导入的闭集合同、test-only 312-case adapter、纯确定性 evaluator；312/312 disposition/gate 与 core/trace/source leaf parity 由 test 侧 oracle 比对，且 runtime 源码静态禁止门为零命中。
- exact-key、NFC/canonical/hash、finite 数值、sorted-unique refs、closed union/disjoint、authority membership、visibility/Query/provenance 五门 fail closed。
- 后续 Work items 2/3 未完成前不得称 D10 runtime accepted；最终须有独立 reviewer、D10 focused、D09 artifact/runtime 相邻与全 R4 回归、compile/Ruff/8911 停止证据。

## Risk Boundaries

- 仅允许上述 Worker-01 新文件写入；其余路径只读。不得修改冻结 D10 artifact 或 D09 及更早实现。
- 不运行网络、浏览器、产品、服务、真实项目或模型；8911 必须保持停止。
- 当前阶段使用已冻结 D10/D09 设计与本地证据，外部框架扫描不会改变最小纯 Python runtime 路径，因此不重新引入依赖或框架。
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.
- A provider catalog/auth/transport preflight is diagnostic, not a live capability verdict: timeout, auth refresh failure, malformed output, or a stale/incomplete catalog must be recorded and followed by one real route attempt. Explicit user-selected routes are not blocked merely because the catalog does not list them; only a missing executable or native transport boundary may stop before that attempt.

## Loop Log

- 2026-08-17 21:32:51: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-17 21:40:00: D10 artifact freeze recorded; runtime decomposed into three serial work items. Worker 01 is the only unlocked write slice.
- 2026-08-18：Worker-01 runtime review 发现 fixture authority 将四个 intentional external source pair 错列为 accepted，并发现 model evidence 删除与 authority gate 时序缺口；按 immutable-completion 规则声明重开而非静默覆盖。
- 2026-08-18：generator-first 修订已完成：312 authority entries 各仅保留一个 accepted pair；catalog extra pair 继续作为攻击输入；runtime/verifier 恢复合法闭集子集语义，并在 `project_facts` 前阻断 source/model/identity/authority mismatch。
- 2026-08-18：Codex 实跑 generator/oracle/verifier、D10 artifact `107 passed`、D10 runtime `30 passed`、D09 `99/145 passed`、compile、外部 SHA anchor 与 8911 停止均通过；独立 Luna/max verifier 返回 `ACCEPT_WORKER01`。Worker 02 现解锁，Worker 03 继续锁定。
- 2026-08-18：Worker-02 经 Pi 实现/纠偏、CodeBuddy 回退修复与三次独立审阅后返回 `ACCEPT_WORKER02`。最终 D10 `118 passed / 11225 subtests`、D09 全量相邻 `243 passed / 33 subtests`、Ruff/compile/8911 停止均通过。权威记录为 `context/medical_monitoring_r4_d10_runtime_worker02_acceptance_20260818.md`；Worker-03 现解锁。
- 2026-08-18：Worker-03 公共导出、replay/anti-overfit/mutation/verifier/static closure 与全量回归完成。独立 reviewer 首次退回不完整 projection 重签证据；完整重算 projection content hash 与 ID 后返回 `ACCEPT_WORKER03`，并明确接受 synthetic/offline D10 runtime。最终 D10 `182/11225`、artifact `107/10`、D09 `243/33`、全 R4 `4268/11258`、Ruff/compile/immutable anchor/8911 停止均通过。权威暂停记录为 `context/medical_monitoring_r4_d10_runtime_final_acceptance_pause_20260818.md`。下一安全动作是 R4 阶段总体关闭评审，不直接跳入 R5。
