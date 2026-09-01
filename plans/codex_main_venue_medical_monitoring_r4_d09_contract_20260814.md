# Codex Main-Venue Plan: medical_monitoring_r4_d09_contract_20260814

Date: 2026-08-14
Objective: 冻结R4-D09中心重复模式与系统性风险的typed合同、分母与coverage门、cutoff/时间窗、分层与可比性、个体证据展开、owner/投影边界及挑战矩阵，保持8911停止且不触碰医学写作或真实项目

## Task Decomposition

1. 两位独立参与者分别从医学监查/监管方法与工程/反过拟合角度挑战本地候选合同。
2. Codex 综合为 v0.1 草案，冻结 owner、identity、完整性顺序、分母与可比性门、五类 disposition、lineage 和投影边界。
3. 对小样本、零风险、单个高风险、重复计数、规则变化、隐藏个体和跨中心不可比做反例审阅。
4. 仅在语义接受后构建 catalog/oracle/registry/generator；合同接受前不写 D09 runtime。

## Source Packet

- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md`
- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md`
- `reviews/medical_monitoring_r4_risk_coverage_matrix_v1_20260810.md`
- `context/medical_monitoring_r4_d09_external_pattern_decision_20260814.md`
- 已接受的 D01-D08 owner/typed input/acceptance records（仅相邻边界）

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_pi_qwen38` | `alibaba` | `qwen3.8-max` | `runs/conference/medical_monitoring_r4_d09_contract_20260814/general_pi_qwen38.md` |
| `general_grok46` | `grok-build` | `grok-4.6` | `runs/conference/medical_monitoring_r4_d09_contract_20260814/general_grok46.md` |

## Conference Panel Coordination

- No sub-venue chair. Codex leads the assigned panel directly.

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- 初始状态：两位 participant 待 dispatch；采用 runner 120 分钟 hard wait，同一 session 补发优先。

## Codex Verification Checklist

- 分子、分母、coverage、时间窗、分层、可比性和来源能逐项追溯。
- 零风险、小样本、单个高风险、重复 revision、规则变化、hidden evidence 均有闭集语义。
- 不生成黑箱总分/排名，不反向改写 D01-D08，不越权生成 D10 项目结论。
- 8911 停止；无真实项目/患者数据；无医学写作或产品 UI 改动。
