# Codex Main-Venue Plan: medical_writing_greenfield_visual_20260714

Date: 2026-07-14
Objective: 复核医学写作绿地建稿与建稿后编辑器在1600x1000桌面端是否延续现有工作台视觉语言、保持文档编辑与AI交互核心地位，并识别任何误导状态、布局冲突或工作流缺口

## Task Decomposition

1. Compare the existing-DOCX editor and greenfield setup/editor at identical desktop viewports.
2. Verify setup, working-copy, structured-table, decision-review, AI, document-map and Word interactions in the live browser.
3. Collect independent three-round visual critiques; qualify any model/tool failures and preserve raw evidence.
4. Resolve recommendations against product contracts and live behavior; rerun full medical-writing tests and desktop QC.
5. Write the clean Codex synthesis and task/handoff records.

## Source Packet

- Existing DOCX reference and greenfield screenshots/metrics under `records/visual_qc_20260714/medical_writing_greenfield_runtime_v4/`.
- UI source: `frontend/src/App.jsx`, `frontend/src/styles.css`.
- Runtime/API source and tests named in the active slice task record.
- Product boundaries: `records/active_slices/medical_writing_greenfield_runtime_20260714/TASK_RECORD.md`.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `visual_aishuo_minimax` | `aishuo` | `MiniMax-M3` | `runs/conference/medical_writing_greenfield_visual_20260714/visual_aishuo_minimax.md` |
| `visual_buddy_kimi` | `buddy` | `kimi-k2.7-code` | `runs/conference/medical_writing_greenfield_visual_20260714/visual_buddy_kimi.md` |
| `visual_opencode_qwen` | `opencode-go` | `qwen3.7-plus` | `runs/conference/medical_writing_greenfield_visual_20260714/visual_opencode_qwen.md` |

## Sub-Venue Review

- No sub-venue chair. Codex leads the visual/design panel directly.

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- MiniMax-M3 and qwen3.7-plus completed three same-session rounds and were incorporated only where supported by live evidence.
- Kimi terminally timed out after 1800 seconds without substantive output; Mimo fallback failed with HTTP 400. Neither was used.
- No late output changed the production patch or Codex acceptance.

## Codex Verification Checklist

- [x] Greenfield setup stays inside the editor column; AI rail and document map remain visible.
- [x] Project fields, 14-section scaffold and unresolved decisions are legible.
- [x] Decision value/reason/source can be resolved and refreshed with optimistic concurrency.
- [x] Structured table insertion, full-screen designer and cell editing work in the same editor.
- [x] Draft Word works and formal Word remains blocked before approval.
- [x] 1600x1000, 1920x1080 and 2048x1024 have no horizontal overflow or column-order regression.
- [x] Full medical-writing suite passes: 182 tests.
- [x] Model failures and rejected recommendations are recorded without being presented as acceptance evidence.
