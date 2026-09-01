# Codex Main-Venue Plan: mw_word_engine_open_source_gate_20260718

Date: 2026-07-18
Objective: Review the no-cost production DOCX generation/export pipeline using current POC evidence and recommend a bounded integration and acceptance plan for the medical-writing subsystem

## Task Decomposition

1. Independently assess the measured POC and license evidence.
2. Separate generation, structural validation, field/index update, deterministic render regression and Word-native acceptance responsibilities.
3. Decide whether validation belongs at runtime, release gate, or both, and define fail/override behavior for generated versus imported documents.
4. Recommend a no-cost implementation and rollback plan.

## Source Packet

Use the source-of-truth list in the conference context. Key measured facts: current exporter 0 schema errors; Aspose 1; Syncfusion 7; LibreOffice round-trip 66. Commercial engines are prohibited by user decision. LibreOffice may remain render-only.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_aishuo_cms` | `aishuo` | `cms-model` | `runs/conference/mw_word_engine_open_source_gate_20260718/general_aishuo_cms.md` |
| `general_opencode_deepseek_flash` | `opencode-go` | `deepseek-v4-flash` | `runs/conference/mw_word_engine_open_source_gate_20260718/general_opencode_deepseek_flash.md` |

## Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_chair_grok45` | `grok-build` | `grok-4.5` | `runs/conference/mw_word_engine_open_source_gate_20260718/general_chair_grok45.md` |

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- Start: 2026-07-18 10:47 CST.
- Every role begins with one complete pass. Slow output remains pending during the hard wait and controlled retry.

## Codex Verification Checklist

- Verify each participant read the actual reports and current source.
- Reject recommendations that require a paid runtime, server-side Word automation, public document upload, or LibreOffice DOCX round-trip.
- Require explicit generated/imported document boundary and rollback behavior.
- Re-run Open XML SDK, exporter tests, LibreOffice render and Word-native acceptance after any integration.
