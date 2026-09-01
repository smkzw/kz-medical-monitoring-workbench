# Codex Main-Venue Plan: medical_writing_editor_formatting_visual_20260714

Date: 2026-07-14
Objective: 审阅医学写作Word式富文本与结构化表格工具栏的桌面交互分组、信息密度、样式边界、表格插入和视觉风险；基于现有2048x1024真实页面与统一rich_text到DOCX契约，不执行生产写入

## Task Decomposition

1. Each visual participant independently inspects the two current screenshots and bounded architecture packet.
2. Each proposes a compact desktop toolbar hierarchy and structured-table insertion interaction.
3. Each challenges density, selection state, popover geometry, editor/AI priority and 1920/2048 failure modes in rounds 2-3.
4. Codex compares outputs, implements the production contract, and owns live browser and Word-render acceptance.

## Source Packet

- `records/active_slices/medical_writing_editor_formatting_20260714/ARCHITECTURE_REVIEW_PACKET.md`
- `records/active_slices/medical_writing_content_quality_20260714/browser_qc/rux_source_content_open_2048x1024.png`
- `records/visual_qc_20260712/medical_writing_real_projects_three/medical_writing_proj_rux_03_002_desktop.png`
- `frontend/AGENTS.md`

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `visual_aishuo_minimax` | `aishuo` | `MiniMax-M3` | `runs/conference/medical_writing_editor_formatting_visual_20260714/visual_aishuo_minimax.md` |
| `visual_buddy_kimi` | `buddy` | `kimi-k2.7-code` | `runs/conference/medical_writing_editor_formatting_visual_20260714/visual_buddy_kimi.md` |
| `visual_opencode_qwen` | `opencode-go` | `qwen3.7-plus` | `runs/conference/medical_writing_editor_formatting_visual_20260714/visual_opencode_qwen.md` |

## Sub-Venue Review

- No sub-venue chair. Codex leads the visual/design panel directly.

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

Record start/end state, same-session round count, pending/failed/incorporated status, fallback/retry reason and whether late outputs were used.

## Codex Verification Checklist

- Prompt preflight passes with no nonexistent or overbroad read path.
- All three roles complete independent three-round same-session outputs or remain explicitly pending under the timeout policy.
- Codex verifies proposed controls against Tiptap schema, working-copy persistence and DOCX mapping before implementation.
- Codex captures and compares real 1920x1080 and 2048x1024 browser states after implementation.
