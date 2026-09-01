# Codex Main-Venue Plan: medical_writing_word_table_visual_20260714

Date: 2026-07-14
Objective: 独立审阅RUX、D001、PNH三个真实研究项目医学写作草稿Word的68张表、259页渲染，重点验证研究流程表跨页重复表头、宽表列宽、合并单元格、普通领域表、长附注、中文字体与页面可审阅性；只返回有页面证据的缺陷或通过结论，不修改生产文件

## Task Decomposition

1. Each participant reads the visual packet and structured QC independently.
2. Each participant inspects all contact sheets, then opens cited original-resolution pages before asserting a defect.
3. Round 2 challenges unsupported findings, missed continuation pages and viewer-artifact confusion.
4. Round 3 returns corrected findings with project/page evidence and a clear pass/fail recommendation.
5. Codex reproduces every claimed defect against original PNG/PDF/OOXML and owns final acceptance.

## Source Packet

- `records/active_slices/medical_writing_word_table_fidelity_20260714/CONFERENCE_VISUAL_PACKET.md`
- `records/active_slices/medical_writing_word_table_fidelity_20260714/reports/word_table_fidelity_cjk_qc.json`
- 17 contact sheets under `reports/contact_sheets_cjk/`
- 24 original-resolution pages listed in the packet under `renders_cjk/`

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `visual_aishuo_minimax` | `aishuo` | `MiniMax-M3` | `runs/conference/medical_writing_word_table_visual_20260714/visual_aishuo_minimax.md` |
| `visual_buddy_kimi` | `buddy` | `kimi-k2.7-code` | `runs/conference/medical_writing_word_table_visual_20260714/visual_buddy_kimi.md` |
| `visual_opencode_qwen` | `opencode-go` | `qwen3.7-plus` | `runs/conference/medical_writing_word_table_visual_20260714/visual_opencode_qwen.md` |

## Sub-Venue Review

- No sub-venue chair. Codex leads the visual/design panel directly.

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- Record each provider/model, same-session round count, session id, start/end time, return code, fallback and failure reason in run/log outputs and final metrics.
- Apply the configured 45-minute large-participant wait and 90-minute main hard wait; do not fail for latency alone.

## Codex Verification Checklist

- Confirm all three PDFs embed a CJK font and the structured report has no failures.
- Inspect every contact sheet and all 24 original-resolution pages directly.
- Reproduce any cited crop, overlap, missing header, missing note or glyph issue.
- Distinguish viewer black padding from actual white PDF page pixels.
- Write review and metrics, run conference validation/review gate, archive temporary sessions, and update subsystem/system task records.
