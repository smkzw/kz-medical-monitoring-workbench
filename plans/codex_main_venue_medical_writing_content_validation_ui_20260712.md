# Codex Main-Venue Plan: medical_writing_content_validation_ui_20260712

Date: 2026-07-12
Objective: 审阅医学写作证据面板中文件内容核验与显式确认交互，确保桌面端严谨、紧凑、无安全扫描残留且不弱化编辑器与AI主工作区

## Task Decomposition

- Verify the content-consistency status hierarchy and explicit override interaction.
- Check desktop density, overflow, editor/AI primacy, audit visibility, and removal of security-scan language.
- Incorporate only recommendations confirmed by Codex browser QC and automated regression.

## Source Packet

- Current component/source, baseline medical-writing screenshot, real RUX content-validation screenshot and QC JSON, and active task record.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `visual_aishuo_minimax` | `aishuo` | `MiniMax-M3` | `runs/conference/medical_writing_content_validation_ui_20260712/visual_aishuo_minimax.md` |
| `visual_buddy_kimi` | `buddy` | `kimi-k2.7-code` | `runs/conference/medical_writing_content_validation_ui_20260712/visual_buddy_kimi.md` |
| `visual_opencode_qwen` | `opencode-go` | `qwen3.7-plus` | `runs/conference/medical_writing_content_validation_ui_20260712/visual_opencode_qwen.md` |
| `visual_opencode_mimo_fallback` | `opencode-go` | `mimo-v2.5` | `runs/conference/medical_writing_content_validation_ui_20260712/visual_opencode_mimo_fallback.md` |

## Sub-Venue Review

- No sub-venue chair. Codex leads the visual/design panel directly.

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- `visual_buddy_kimi`: terminal failure after the configured 1800-second hard wait; runner also exposed a timeout bytes/str exception. No substantive output incorporated.
- `visual_opencode_mimo_fallback`: activated under the user-approved Kimi fallback rule.
- `visual_opencode_mimo_fallback`: provider returned HTTP 400 while reading the screenshot and no usable Hermes session was established; excluded.
- Incorporated outputs: MiniMax and Qwen. Final visual/browser acceptance: Codex.

## Codex Verification Checklist

- Verify a real confirmed document and an isolated real-file mismatch at 1600x1000.
- Verify reason-only cannot enable confirmation; every current warning must be checked.
- Verify confirmed-after-warning state and reason are visible and audited.
- Verify no horizontal overflow, no security-scan language, and no production-state mutation from failure-branch QC.
- Result: all checklist items passed. Evidence is recorded in `reviews/codex_conference_medical_writing_content_validation_ui_20260712_review.md` and `records/visual_qc_20260712/medical_writing_reference_override/`.
