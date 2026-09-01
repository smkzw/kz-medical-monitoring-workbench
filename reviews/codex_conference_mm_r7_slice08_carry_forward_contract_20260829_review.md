# Codex Conference Review: mm_r7_slice08_carry_forward_contract_20260829

Date: 2026-08-29

## Verdict

`ACCEPT_R7_SLICE_08_CONTRACT_V0_2` — v0.1 保留为被纠偏证据，v0.2 冻结为 08A 实施权威。

## Boundary Compliance

Hermes workflow guard 的只读会商边界得到遵守。参与者只读取合同、Round-1 输出和已声明源码证据；未修改产品源码，未运行真实项目、产品服务或医学模型，8911/5174 保持停止。

## Participant Outputs Reviewed

- Round 1：`general_single_object.md`，结论 `REVISE`，提出七类可执行纠偏。
- Round 2：同一 session `01a04bd9-3108-7000-9a27-84fd71893719` 的 `general_single_object_round2.md`，结论 `ACCEPT_R7_SLICE_08_CONTRACT_V0_2`。

## Conference Panel Review

Round 1 识别了风险缺行误关闭、平行风险状态机、规则影响过宽、artifact 沿用未反查、迁移/CAS 不明确、三模式字段未冻结和中文泄漏门不足。Codex 没有照抄建议，而是复核当前 R1/R2/R6/R7 源码后形成 v0.2：保留 R2 唯一生命周期，R7 只做 `RiskChangeKind`；data listing/Journey 不作为沿用产物；迁移最小化为两个表并复用既有 ResultPublication。

## Main-Venue Codex Review

v0.2 与现有产品顺序一致：08A 领域事实面与加法迁移，08B R5/R6/CAS 接线，08C 中文投影与 ego(lite)，08D 三模式综合回归。合同不把 synthetic 证据外推到真实医学质量、R7 总体或 R8。

## Codex Independent Verification

Codex 亲自核对：R1 `ae_mh.py` 的高危缺行不自动关闭；R2 `risk.py` 的唯一生命周期/合法转移；R6 `mode_output.py` 的 carry-forward 与 fixed-total 门；R7 `launch_registry.py` 的 v2 additive migration、busy timeout、显式事务和 ResultPublication。当前只冻结合同，未运行实现测试或视觉验收。

## Final Decision

冻结 `reviews/medical_monitoring_r7_slice08_three_mode_carry_forward_contract_v0_2_20260829.md`。解锁 08A；不得提前改 UI、运行真实项目或声称 R7 完成。
