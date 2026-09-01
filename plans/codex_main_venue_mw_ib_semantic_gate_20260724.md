# Codex Main-Venue Plan: mw_ib_semantic_gate_20260724

Date: TODO
Objective: 基于真实MY004研究者手册独立AI提取结果，设计并复核医学事实语义门：既往试验事实不得污染当前方案设计；测试剂量不得等同RP2D；IB版本不得覆盖方案版本；随后形成可执行修复与真实重测标准。仅做功能和医学科学性，不做工程安全审计。

## Task Decomposition

TODO

## Source Packet

TODO

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_aishuo_cms` | `aishuo` | `cms-model` | `runs/conference/mw_ib_semantic_gate_20260724/general_aishuo_cms.md` |
| `general_opencode_deepseek_flash` | `opencode-go` | `deepseek-v4-flash` | `runs/conference/mw_ib_semantic_gate_20260724/general_opencode_deepseek_flash.md` |

## Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_chair_grok45` | `grok-build` | `grok-4.5` | `runs/conference/mw_ib_semantic_gate_20260724/general_chair_grok45.md` |

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

TODO: Record start/end time, pending/failed/incorporated status, retry reason, and whether late outputs were used.

## Codex Verification Checklist

TODO
