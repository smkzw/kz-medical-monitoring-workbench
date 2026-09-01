# Codex Main-Venue Plan: mm_r6_contract_acceptance_conference_v0_1_20260827

Date: 2026-08-27
Objective: 独立挑战并裁决 R6 外部报告审阅与三模式输出合同稳定字节：核对 prose、contract.json、challenge_matrix.json 的闭合性、实现可行性、枚举/身份/coverage/三件套/修订diff/三模式/错误语义一致性；仅合同审阅，不修改文件、不启动服务或真实项目。

## Task Decomposition

1. 对账三份候选工件的字段、枚举、计数、错误语义和身份边界。
2. 由两个不同 provider/model 独立挑战可实现性、遗漏面、修订 diff、三件套和模式隔离。
3. 对阻断项执行同 session 定向复核；Codex 修订后再做稳定字节确定性验收。

## Source Packet

- System Design v1.1 §§13–14。
- R0–R8 实施计划 §10。
- R6 prose 合同、`contract.json`、`challenge_matrix.json`。
- R6 冻结上下文与三个 execution worker 报告。

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_pi_antigravity` | `google-antigravity` | `gemini-3.7-flash` | `runs/conference/mm_r6_contract_acceptance_conference_v0_1_20260827/general_pi_antigravity.md` |
| `general_grok46` | `grok-build` | `grok-4.6` | `runs/conference/mm_r6_contract_acceptance_conference_v0_1_20260827/general_grok46.md` |

## Conference Panel Coordination

- No sub-venue chair. Codex leads the assigned panel directly.

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- Gemini：初始完整 pass 后进行一次同 session 定向复核；最终意见已采用。
- Grok：初始完整 pass 后进行两轮同 session 定向复核；最终 round 3 的 MUST 1–3
  已实施，条件式撤回异议已采用。
- 无 provider 替换；无超时重派；每个角色始终复用原 session。

## Codex Verification Checklist

- 重新计算三份最终工件 SHA-256。
- 校验 86 行唯一 ID、分类/严重度计数、49 个诊断码逐码映射和 11 个验证器。
- 校验 reverse expected surface/link 分离、完整审阅门、稳定身份与 R6C-006 block 语义。
- 复核执行审计、会商路由身份和 8911/5174 停止状态。
