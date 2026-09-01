# Codex Main-Venue Plan: medical_writing_visible_table_editor_20260714

Date: 2026-07-14
Objective: 复核医学写作工作台中研究流程表及其他方案表格的同步可见性、信息层级、桌面端可审阅性、表格选择定位与复杂宽表交互；基于三项目真实截图和DOM一致性报告提出可执行缺陷，Codex负责最终验收

## Task Decomposition

1. Verify data fidelity and interaction wiring independently from aesthetics.
2. Inspect all three real-project desktop screenshots at original resolution.
3. Ask each visual participant for an independent three-round critique with no chair or cross-reading.
4. Compare recurring findings against actual source and the user's desktop-first/editor-first boundaries.
5. Apply only concrete, evidenced corrections; rerun DOM parity, tests, build and screenshots after any accepted edit.

## Source Packet

- Three original-resolution 1600x1000 screenshots under `output/medical-writing-table-sync-qc/`.
- The corresponding JSON report proving 68 tables, 3,748 visible cells and 146 notes match API source with zero failures.
- Current `App.jsx`, `styles.css`, and active-slice task record.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `visual_aishuo_minimax` | `aishuo` | `MiniMax-M3` | `runs/conference/medical_writing_visible_table_editor_20260714/visual_aishuo_minimax.md` |
| `visual_buddy_kimi` | `buddy` | `kimi-k2.7-code` | `runs/conference/medical_writing_visible_table_editor_20260714/visual_buddy_kimi.md` |
| `visual_opencode_qwen` | `opencode-go` | `qwen3.7-plus` | `runs/conference/medical_writing_visible_table_editor_20260714/visual_opencode_qwen.md` |

## Sub-Venue Review

- No sub-venue chair. Codex leads the visual/design panel directly.

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- Record per-role session id, provider/model, three-round evidence, start/end time, status and any fallback in conference logs and metrics.
- Slow output remains pending under the configured policy; no fallback is activated solely for latency.

## Codex Verification Checklist

- [ ] Three screenshots inspected at original resolution by Codex.
- [ ] Three participant outputs preserve independent three-round sessions.
- [ ] Accepted recommendations trace to screenshot/report/source evidence.
- [ ] No recommendation hides or summarizes away real table/notes.
- [ ] Final DOM parity report remains zero-failure after edits.
- [ ] Full pytest, compileall and frontend build pass.
