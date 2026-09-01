这是同一 Pi 会话的 D08 合同第三轮定向复审，不得新开会话、不得编辑任何文件。

Read these files only:
1. 你上一轮报告 `runs/conference/medical_monitoring_r4_d08_contract_20260814/general_pi_qwen38_round2.md`；
2. 修订稿 `reviews/medical_monitoring_r4_d08_cross_domain_logic_slice_contract_v0_3_20260814.md`；
3. 冻结矩阵 `reviews/medical_monitoring_r4_risk_coverage_matrix_v1_20260810.md`。

## Hard boundaries

- 只读临床/数据逻辑复审；无实现、无服务/8911、无真实项目/数据/provider、无 UI/医学写作/系统安全工作。
- 复用既有 session；不得读取另一参与者报告。

逐项重测上一轮 residual A-D，并额外检查：Evaluation unit_id 含 lineage/version 而 D08UnitStableCore/PublicR4RiskIdentity 独立承接跨 run 连续性，是否已明确且不与冻结矩阵冲突；cutoff、temporal result→L1 闭表、upstream L1 非自动继承是否单值可执行。不得重开已关闭问题，除非给出 v0.3 内部可复现的两读反例。

只返回以下之一：
- `ACCEPT_D08_DRAFT_FOR_FREEZE_ARTIFACT_BUILD`：合同语义已足以进入 catalog/oracle/registry/generator 构建，但不等于 `ACCEPT_D08_CONTRACT`、不授权 runtime；
- `REVISE_D08_DRAFT`：列出最小反例、冲突原文和精确修文。

保持原角色、证据/推断/建议/不确定性分区。Codex 是最终裁决者。

Write exactly one output file:

runs/conference/medical_monitoring_r4_d08_contract_20260814/general_pi_qwen38_round3.md

The runner persists the report; return the complete report only.
