# R4-D05 合成/离线纵切合同接受记录

Date: 2026-08-12  
Status: `ACCEPTED_FROZEN_R4_D05_CONTRACT_V1_2`

## 接受对象

- 合同：`reviews/medical_monitoring_r4_d05_visit_schedule_slice_contract_v1_20260812.md`
- 独立接受的 v1.1 临床/算法语义 SHA-256：`7d20dadd112c9f2b8573afdbd004787588d70aa73697c41b01e9d45947f7c4fa`
- 独立接受的 v1.2 路径勘误 SHA-256：`0c7eb9d5bd9e3fc9ab845715ba2121249ce99d56ee3c11edf7404fa2aae9c265`
- Codex 写入顶部 status 与末尾 freeze record 后的最终文件 SHA-256：`23172cac905b3b152937976a7ee5d7eb895bac274ced7fc40a49b5f7a205921c`
- v1.2 只把授权实现路径从误写的 R1 更正为权威 R4 package；勘误接受后的变更仅为两处冻结元数据。

## 独立反证链

同一 Codex Luna CLI compatibility session：`019ff2c3-128a-7471-bedd-2894201fdf32`。

1. v1 `b90b7a3483e5a6fa565d25794235f6ebfe8b6580722e612d41834a11001427e3`：`REVISE`，发现 7 个阻断项；
2. v1.1 `b1060e824768463ab0d506e3e6ba4e4586b9091a1933b5d36c5a73589b605ebe`：7 项关闭，但 priority precedence 仍 `PARTIAL`，结论 `REVISE`；
3. v1.1 `7d20dadd112c9f2b8573afdbd004787588d70aa73697c41b01e9d45947f7c4fa`：priority 与 gate truth table 全部 `CLOSED`，最终 `ACCEPT`。
4. v1.2 `0c7eb9d5bd9e3fc9ab845715ba2121249ce99d56ee3c11edf7404fa2aae9c265`：实现前文件系统核查触发路径勘误，同 session 核对 R4 README 与合同后 `ACCEPT_PATH_ERRATUM`。

报告：

- `runs/codex-subagent_medical_monitoring_r4_d05_contract_20260812.md`
- `runs/codex-subagent_medical_monitoring_r4_d05_contract_20260812_followup1.md`
- `runs/codex-subagent_medical_monitoring_r4_d05_contract_20260812_followup2.md`
- `runs/codex-subagent_medical_monitoring_r4_d05_contract_20260812_followup3.md`

## 关闭的阻断项

1. chained anchor 在 expected-set 前解析；
2. `snapshot_as_of` 与 `clinical_event_cutoff` 双范围；
3. applicability/routing/anchor/cutoff `ScheduleGate` 及独立对账；
4. 多日/多接触 `ActualEncounterBundle`；
5. 活动级双向 assignment 与 consumption ledger；
6. enrollment-aware Query context；
7. D03/D04 等 producer 的精确 typed anchor；
8. 明确 maturity rule、Journey 待定/out-of-cutoff 锚点、可重放 interpretation ledger；
9. priority first-match precedence 与 ScheduleGate 合法状态真值表。

## 接受范围与保留边界

接受仅限 synthetic/offline D05 合同语义和 116 行挑战矩阵，可进入有界实现。它不接受或证明 D05 代码、R4 总体、R5 Patient Journey UI、真实项目、真实模型/provider、正式 PD、中心/项目聚合、产品或生产。

继续保持：8911 停止；不运行真实项目；不修改医学写作子系统；不扩展系统安全设计/测试。

## 下一安全动作

按本合同建立 D05 有界执行包，只允许在 `poc/medical_monitoring_ai_native_r4` 合成/离线 R4 surface 新增访视计划对象、gate、bundle、assignment/ledger、evaluator、Query/Journey projection、fixtures 与测试；公共 R4 文件仅作最小兼容适配，并跑 D01-D04、R2、R3 相邻回归。实现完成后另做不可变快照独立验收。
