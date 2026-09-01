# Codex Main-Venue Plan: monitoring_incremental_diff_architecture_20260712

Date: 2026-07-12
Objective: Review two-real-project monitoring listing batch-diff evidence, challenge row-key/schema/persistence/audit boundaries, and recommend a production-grade incremental diff architecture and TDD slice without reading raw clinical row values.

## Task Decomposition

1. Challenge source/key/schema observations independently from backend, Chinese clinical/product and workflow/governance perspectives.
2. Exact `aishuo/MiniMax-M3` compares participant outputs and identifies unresolved conflicts.
3. Codex verifies claims against current code and aggregate-only real-source probes.
4. Land only the accepted TDD plan; no real-project upload exposure before implementation and regression.

## Source Packet

Use only the source list in the conference context. Original Excel bytes and raw clinical row values are excluded.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_buddy_deepseek` | `buddy` | `deepseek-v4-pro` | `runs/conference/monitoring_incremental_diff_architecture_20260712/general_buddy_deepseek.md` |
| `general_opencode_mimo` | `opencode-go` | `mimo-v2.5` | `runs/conference/monitoring_incremental_diff_architecture_20260712/general_opencode_mimo.md` |
| `general_buddy_glm` | `buddy` | `glm-5.2` | `runs/conference/monitoring_incremental_diff_architecture_20260712/general_buddy_glm.md` |

## Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_aishuo_minimax` | `aishuo` | `MiniMax-M3` | `runs/conference/monitoring_incremental_diff_architecture_20260712/general_aishuo_minimax.md` |

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

Record provider/model/session/round markers, duration, retry/fallback, and whether late outputs were incorporated.

## Codex Verification Checklist

- Existing service uses demo fallback and does not compare prior batch rows.
- RUX and MY009 each have a real baseline/new batch pair.
- RUX representative sheets prove one universal composite key is unsafe.
- MY009 demonstrates sheet additions and header formatting drift.
- No recommendation may equate listing diff with EDC audit history or auto-approve medical mappings.
