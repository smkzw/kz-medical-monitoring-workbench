# Codex Main-Venue Plan: mw-ai-generalization-batch-ux-r32

Date: TODO
Objective: 独立审阅医学写作工作台当前综合AI提示词的跨适应症精确泛化、避免项目过拟合，以及正常用户路径中的批量确认/逐项确认边界；仅报告增量冲突和高风险，不修改源码，不重复A1真实E2E测试

## Task Decomposition

TODO

## Source Packet

TODO

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_aishuo_cms` | `aishuo` | `cms-model` | `runs/conference/mw-ai-generalization-batch-ux-r32/general_aishuo_cms.md` |
| `general_codebuddy_deepseek_pro` | `codebuddy-cli` | `deepseek-v4-pro` | `runs/conference/mw-ai-generalization-batch-ux-r32/general_codebuddy_deepseek_pro.md` |

## Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_chair_pi_qwen38` | `alibaba` | `qwen3.8-max-preview` | `runs/conference/mw-ai-generalization-batch-ux-r32/general_chair_pi_qwen38.md` |

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

TODO: Record start/end time, pending/failed/incorporated status, retry reason, and whether late outputs were used.

## Codex Verification Checklist

TODO
