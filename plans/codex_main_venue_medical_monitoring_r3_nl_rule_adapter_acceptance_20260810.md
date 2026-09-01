# Codex Main-Venue Plan: medical_monitoring_r3_nl_rule_adapter_acceptance_20260810

Date: 2026-08-10
Objective: 独立验收医学监查 R3 中文自然语言规则适配器：功能正确性、R1-R3身份闭环、候选隔离、中文原生作用范围与冻结边界；不做安全性设计测试，不运行真实项目或服务

## Task Decomposition

1. 冻结并校验 rule-AI 13 文件摘要及 R1/R2/R3 上游锚点。
2. 两位 participant 在隔离上下文中分别完成源级反证、全量测试与中文用户语义审查。
3. Codex 比对两个独立结论，复现任何 VETO；必要时仅在同一 participant session 做定向续问。
4. 仅在无 P0-P4 阻断且决定性检查全绿时接受该切片，随后收口执行/会商记录并进入 R4。

## Source Packet

- `context/medical_monitoring_r3_nl_rule_adapter_acceptance_20260810_conference_context.md`
- Design v1.1、R0-R8 实施计划 v1.1 的 R3 条款。
- `poc/medical_monitoring_ai_native_r3_rule_ai/**` 13 文件冻结快照。
- 冻结 R1/R2/R3 只读公开合同与摘要；不运行 R1 全量。

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_pi_qwen38` | `alibaba` | `qwen3.8-max` | `runs/conference/medical_monitoring_r3_nl_rule_adapter_acceptance_20260810/general_pi_qwen38.md` |
| `general_grok45` | `grok-build` | `grok-4.5` | `runs/conference/medical_monitoring_r3_nl_rule_adapter_acceptance_20260810/general_grok45.md` |

## Conference Panel Coordination

- No sub-venue chair. Codex leads the assigned panel directly.

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- 两位 participant 并行，各 120 分钟 hard wait；慢输出保持 pending，不重复派发。
- 仅在终态输出存在具体遗漏时使用同 session follow-up；记录 session、route、fallback 和终态。

## Codex Verification Checklist

- [x] 主会场 rule-AI `246 passed`、R3 `339 passed`、Ruff/编译/锚点/8911/cache。
- [x] 纠正测试类重名导致的反例漏收集；收集数由 245 变为 246。
- [x] 恢复 R1 测试副作用污染的截图并重建 `ba6692f...` 全树锚点。
- [x] 两位可执行独立路线均返回最终 ACCEPT；Grok cancelled 与 Cursor 场地证据 VETO 单独保留。
- [x] 所有 P0-P4 由主会场复现、修正或按明确合同边界处置。
- [x] 最终 review/metrics 三项 review-gate 通过；执行过程文件归档；会商证据保留。
