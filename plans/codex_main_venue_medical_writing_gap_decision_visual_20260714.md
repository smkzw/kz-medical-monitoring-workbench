# Codex Main-Venue Plan: medical_writing_gap_decision_visual_20260714

Date: 2026-07-14
Objective: 对照现有医学写作工作台，对新建医学写作Gap决策页进行桌面端视觉、信息密度、中文临床产品语境和交互可读性复核，提出可直接修订的问题

## Task Decomposition

1. Inspect the same-viewport side-by-side comparison and individual original screenshots.
2. Compare shell dimensions, visual tokens, hierarchy, density and interaction emphasis.
3. Inspect completed/restored states and the QC JSON for state visibility and overflow evidence.
4. Review only the relevant HTML/CSS/JS when a screenshot observation needs selector-level confirmation.
5. Return a prioritized fix list; Codex decides and reruns browser QC.

## Source Packet

The exact screenshot, QC and source files listed in the conference context. No live browser or unlisted production source.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `visual_aishuo_minimax` | `aishuo` | `MiniMax-M3` | `runs/conference/medical_writing_gap_decision_visual_20260714/visual_aishuo_minimax.md` |
| `visual_buddy_kimi` | `buddy` | `kimi-k2.7-code` | `runs/conference/medical_writing_gap_decision_visual_20260714/visual_buddy_kimi.md` |
| `visual_opencode_qwen` | `opencode-go` | `qwen3.7-plus` | `runs/conference/medical_writing_gap_decision_visual_20260714/visual_opencode_qwen.md` |

## Sub-Venue Review

- No sub-venue chair. Codex leads the visual/design panel directly.

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

Record one stable session per role, three non-empty rounds, duration, fallback and terminal failures. Slow remains pending under the global rule.

## Codex Verification Checklist

- Compare reference and prototype in one screenshot at identical viewport.
- Verify 1600x1000, 1920x1080 and 2048x1024 no-overflow evidence.
- Verify all 8 questions, 24 options, progress, local persistence, summary and accurate 273x57 logo.
- Re-run browser QC after any accepted visual patch.
- Inspect final screenshots at original detail; Codex owns acceptance.
