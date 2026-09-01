# R4-D10 合同冻结接受记录

日期：2026-08-16  
状态：`FROZEN_R4_D10_CONTRACT_V0_6`

## 最终接受对象

- 合同：`reviews/medical_monitoring_r4_d10_project_signal_slice_contract_v0_6_20260816.md`
- SHA-256：`c613bb7cad82caa6fa477ee2dd28bfca48b805b73503c646401a0aa237deff95`
- 外部模式决策：`context/medical_monitoring_r4_d10_external_pattern_decision_20260816.md`
- Codex 复核：`reviews/codex_medical_monitoring_r4_d10_contract_20260816_review.md`

## 独立审阅链

同一隔离 native Codex Luna/max reviewer session `/root/d10_contract_review` 连续审阅固定快照：

1. v0.1 `REVISE_D10_DRAFT`：15 项；
2. v0.2 `REVISE_D10_DRAFT`：13 项；
3. v0.3 `REVISE_D10_DRAFT`：6 项；
4. v0.4 `REVISE_D10_DRAFT`：5 项；
5. v0.5 `REVISE_D10_DRAFT`：2 项；
6. v0.6 `ACCEPT_D10_DRAFT_FOR_REVISION_FREEZE`。

接受轮首尾 SHA 一致；8911 首尾均无监听；审阅者未修改文件、未启动服务、未读取真实项目或医学写作。

## 冻结的关键边界

- D10 是项目/跨中心聚合 owner，但不重算 D01-D09 个体/中心医学语义。
- 五类信号：项目风险分布、跨中心模式、项目历时趋势、项目安全趋势、项目疗效趋势。
- 正式安全信号、确证治疗效果、最终获益-风险、中心质量裁决不属于 D10。
- 每个比例/率/估计保留成员、绝对量、分母、暴露/随访、coverage、方法和来源，可独立复算。
- 跨中心异常只作优先核查证据，不生成黑箱总分、惩罚性排名或中心好坏结论。
- initial full 只显示“初始全量”；非数据变化不能冒充临床改善/恶化。
- D09 parent/descendant、measure/source risk、gap/opportunity 采用 typed origin/provenance 和分叶计量，禁止重复贡献。
- 盲态/visibility、Query、projection、deep-link、R2 lifecycle、cutoff advance 与多模型证据均 fail closed、内容寻址且可重建。
- artifact 阶段下限为 312 个互斥 primary synthetic cases，并含 mandatory-attack 子配额。

## 接受范围与下一安全动作

本记录只接受合同。未接受 artifact/catalog/oracle/registry/generator、runtime、R5 UI、真实项目/模型、产品、生产、正式临床结论或医学写作。

下一安全动作仅为：按冻结 v0.6 构建 D10 synthetic/offline catalog、独立 oracle、registry、generator 与 quota manifest；完成独立 artifact freeze review 前，不得实现 D10 runtime。8911 必须继续停止。
