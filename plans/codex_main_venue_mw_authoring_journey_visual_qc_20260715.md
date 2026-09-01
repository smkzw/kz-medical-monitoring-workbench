# Codex Main-Venue Plan: mw_authoring_journey_visual_qc_20260715

Date: 2026-07-15
Objective: 复核医学写作从零建项到竞品检索、语料准入与建稿的真实桌面端浏览器旅程，识别有证据的视觉、交互和临床方案写作工作流问题，由Codex进行最终验收

## Task Decomposition

1. Independently inspect the complete 1366px journey and the 1920px editor endpoint at original resolution.
2. Cross-check visible states against the QC metrics and the persisted journey/backend boundary.
3. Challenge findings for evidence quality, scope creep, and contradictions with the user's desktop-first and editor-first requirements.
4. Return a corrected, prioritized review. Codex then verifies each accepted item against the live browser and code before any production write.

## Source Packet

The bounded source packet is defined in `context/mw_authoring_journey_visual_qc_20260715_conference_context.md`: eight final screenshots, one machine-readable QC report, the active task record, and only the directly relevant frontend/backend files.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `visual_aishuo_minimax` | `aishuo` | `MiniMax-M3` | `runs/conference/mw_authoring_journey_visual_qc_20260715/visual_aishuo_minimax.md` |
| `visual_aishuo_gpt55` | `aishuo-gpt55` | `gpt-5.5` | `runs/conference/mw_authoring_journey_visual_qc_20260715/visual_aishuo_gpt55.md` |

## Sub-Venue Review

- No sub-venue chair. Codex leads the visual/design panel directly.

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- Soft wait 20 minutes; large participant wait 45 minutes; hard wait 90 minutes plus one retry.
- Record session id, provider/model, rounds completed, continuation evidence, fallback activation, failure reason, start/end time, and whether the output was incorporated.

## Codex Verification Checklist

- Confirm both outputs are independent and each contains three same-session rounds.
- Inspect the final screenshots directly; do not accept a participant's visual claim without pixel-level confirmation.
- Reject suggestions that recreate dashboard clutter, make override the normal path, or move the document editor away from the core post-creation surface.
- If a change is accepted, run targeted unit tests, Vite build, the desktop browser QC journey, and original-resolution screenshot inspection.
- Update the active task record with accepted/rejected findings and the next LOOP hypothesis.
