# Codex Main-Venue Plan: mm_r7_slice07c3_publication_contract_20260829

Date: 2026-08-29
Objective: 独立审阅并纠偏 R7 Slice-07C-3 synthetic/offline ResultPublication 合同：原子发布、R6 receipts 门禁、现有 R5 S4 builder 与产品 R5AuthorityPacket 的唯一复用路径、progress 发布状态、result-entry 四元组/站点覆盖、幂等冲突和可恢复失败；不修改源码。

## Task Decomposition

1. 核对 07C 上位合同、07C-2 接受边界和当前 R5/R6/R7 实现事实。
2. 由独立会商对象挑战 publication identity、门禁、状态机、迁移与公开 DTO。
3. Codex 仅修订合同，保持源码、服务、真实项目和医学写作不变。
4. 在同一会话复审直至无 P0-P2 阻断，随后冻结合同并运行治理门禁。

## Source Packet

- 上位 Slice-07C v0.2、07C-3 v0.1/v0.2、07C-2 接受记录。
- 当前 R5 S4 builder/validator、R6 receipt 分类、R7 runtime/launch/product router 与测试。

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_single_object` | `codebuddy-cli` | `deepseek-v4-flash` | `runs/conference/mm_r7_slice07c3_publication_contract_20260829/general_single_object.md` |

## Conference Panel Coordination

- No sub-venue chair. Codex leads the assigned panel directly.

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- 同一 CodeBuddy session `ee449ae8-e72f-4c61-ab8f-692415599dc5` 完成三轮。
- Round 1/2 均为可执行纠偏；Round 3 为 `ACCEPT`。无 fallback、无超时、无迟到输出。

## Codex Verification Checklist

- 核对每轮报告、session/model/provider identity 与 runner 日志。
- 核对最终合同已吸收两轮全部 P0-P2，并只保留已关闭的措辞建议。
- 运行 `validate-conference` 与 `review-gate`；不以会商自信替代 Codex 源文件复核。
