# Codex Main-Venue Plan: monitoring_content_confirmation_ui_v1

Date: 2026-07-13
Objective: 在医学监查桌面上传门禁中加入文件内容一致性提示、逐项确认和确认后重试，复用既有写作核验交互并保持高信息密度

## Task Decomposition

1. Compare the current monitoring upload gate and existing writing-reference confirmation interaction.
2. Agree on the smallest inline desktop pattern; do not redesign unrelated monitoring surfaces.
3. Implement API-state handling, acknowledgement state, reason, confirmation call, and one automatic retry.
4. Add interaction tests, build, then compare same-state desktop screenshots at 1600x1000 and 1920x1080.

## Source Packet

See `context/monitoring_content_confirmation_ui_v1_conference_context.md`.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `visual_aishuo_minimax` | `aishuo` | `MiniMax-M3` | `runs/conference/monitoring_content_confirmation_ui_v1/visual_aishuo_minimax.md` |
| `visual_buddy_kimi` | `buddy` | `kimi-k2.7-code` | `runs/conference/monitoring_content_confirmation_ui_v1/visual_buddy_kimi.md` |
| `visual_opencode_qwen` | `opencode-go` | `qwen3.7-plus` | `runs/conference/monitoring_content_confirmation_ui_v1/visual_opencode_qwen.md` |

## Sub-Venue Review

- No sub-venue chair. Codex leads the visual/design panel directly.

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

TODO: Record start/end time, pending/failed/incorporated status, retry reason, and whether late outputs were used.

## Codex Verification Checklist

TODO
