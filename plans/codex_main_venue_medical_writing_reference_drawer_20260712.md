# Codex Main-Venue Plan: medical_writing_reference_drawer_20260712

Date: 2026-07-12
Objective: Design and review a desktop-first competitor protocol reference drawer integrated into the existing medical-writing editor and AI rail, covering discovery, medical relevance, document status, pending translation review, approved evidence insertion, source traceability and invalidation without displacing document editing or AI interaction.

## Task Decomposition

1. Inspect the current RUX/D001 editor-first desktop surfaces and existing design tokens.
2. Independently design the evidence-drawer information architecture and full interaction/state matrix.
3. Reconcile Kimi/GLM/Qwen proposals through exact aishuo review.
4. Codex implements the accepted design, runs Chinese label review, browser interaction QC and reference-vs-current screenshot comparison.

## Source Packet

- Current RUX and D001 desktop screenshots.
- Existing `MedicalWritingPage`, API contracts and production backend states.
- Product authorization/task record and prior production conference review.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `visual_buddy_kimi` | `buddy` | `kimi-k2.7-code` | `runs/conference/medical_writing_reference_drawer_20260712/visual_buddy_kimi.md` |
| `visual_buddy_glm` | `buddy` | `glm-5.2` | `runs/conference/medical_writing_reference_drawer_20260712/visual_buddy_glm.md` |
| `visual_opencode_qwen` | `opencode-go` | `qwen3.7-plus` | `runs/conference/medical_writing_reference_drawer_20260712/visual_opencode_qwen.md` |

## Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `visual_aishuo_minimax` | `aishuo` | `MiniMax-M3` | `runs/conference/medical_writing_reference_drawer_20260712/visual_aishuo_minimax.md` |

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

TODO: Record start/end time, pending/failed/incorporated status, retry reason, and whether late outputs were used.

## Codex Verification Checklist

- Editor and AI remain first-viewport core surfaces.
- All discovery/review/admission/invalidation states and controls are represented.
- Existing brand/logo/design tokens are reused.
- No text overflow, nested cards or page horizontal overflow at desktop acceptance viewport.
- Chinese clinical labels pass separate DeepSeek review.
