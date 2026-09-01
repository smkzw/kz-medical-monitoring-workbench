# Codex Main-Venue Plan: monitoring_source_fragment_visual_qc_20260713

Date: 2026-07-13
Objective: Validate the RUX-03-002 and MY009-UC medical-monitoring desktop flow at 2048x1024, covering source evidence, project/filter hierarchy, and the seven-column sortable/filterable risk checklist

## Task Decomposition

1. Reopen both real projects and verify source-content-first evidence panels.
2. Verify the project information strip, compact bottom boundary note, and desktop layout.
3. Verify the exact seven checklist columns and every sort/filter interaction.
4. Check project-agnostic risk-category semantics on RUX and MY009.
5. Run independent three-round visual panel review, then accept only findings grounded in the current screenshots or source.
6. Re-run focused tests/build and persist system/subsystem logs.

## Source Packet

- `frontend/src/App.jsx`
- `frontend/src/styles.css`
- `tests/test_frontend_unified_risk_workbench_contract.py`
- `output/playwright/monitoring_source_fragment_visual_qc_20260713/09_rux_lab_source_summaries_2048x1024.png`
- `output/playwright/monitoring_source_fragment_visual_qc_20260713/10_my009_lab_source_summaries_final_2048x1024.png`
- `output/playwright/monitoring_source_fragment_visual_qc_20260713/15_rux_checklist_7_columns_2048x1024.png`
- `output/playwright/monitoring_source_fragment_visual_qc_20260713/16_my009_checklist_7_columns_2048x1024.png`

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `visual_aishuo_minimax` | `aishuo` | `MiniMax-M3` | `runs/conference/monitoring_source_fragment_visual_qc_20260713/visual_aishuo_minimax.md` |
| `visual_buddy_kimi` | `buddy` | `kimi-k2.7-code` | `runs/conference/monitoring_source_fragment_visual_qc_20260713/visual_buddy_kimi.md` |
| `visual_opencode_qwen` | `opencode-go` | `qwen3.7-plus` | `runs/conference/monitoring_source_fragment_visual_qc_20260713/visual_opencode_qwen.md` |

## Sub-Venue Review

- No sub-venue chair. Codex leads the visual/design panel directly.

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- Qwen completed three same-session rounds and was selectively incorporated. MiniMax and Kimi were terminated and excluded after explicit boundary violations; exact reasons and temporary-file cleanup are recorded in metrics/review.

## Codex Verification Checklist

- [x] RUX and MY009 real-project runtime state opened.
- [x] Exact seven columns rendered; removed redundant columns absent.
- [x] Seven sort controls and seven filters exercised.
- [x] RUX page/table horizontal overflow zero at 2048x1024.
- [x] MY009 page/table horizontal overflow zero at 2048x1024.
- [x] MY009 adherence category corrected to 用药依从性.
- [x] Risk row opens the existing evidence workspace.
- [x] Application console error count zero.
- [x] Participant findings reviewed and accepted/rejected with evidence.
- [x] Focused tests and production build re-run after final accepted edits.
