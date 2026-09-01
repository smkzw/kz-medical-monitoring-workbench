# Codex Main-Venue Plan: medical_writing_table_ai_revision_20260714

Date: 2026-07-14
Objective: 为医学写作结构化表格建立单元格级独立AI细节修订、医学审阅批准与显式应用闭环，保持来源、版本、审计和Word工作副本一致

## Task Decomposition

1. Review current paragraph revision and structured-table contracts; define a canonical cell anchor and version/source boundary.
2. Run three-round independent conference reviews and GLM chair synthesis; Codex decides the bounded contract.
3. Add server-side table-cell normalization, AI source/context construction, approved application branch and audit detail without changing paragraph behavior.
4. Add table-designer cell-selection callback and cell-scoped AI review UI; no paragraph fallback.
5. Add successful/destructive API/repository/frontend tests, then use at least two real protocol projects in isolated runtime.
6. Verify Word preview, desktop browser flow, cross-project isolation, full relevant regression/build and logs.

## Source Packet

- Full conference context, including current contracts, implementation facts, risk boundaries and explicit questions.
- Existing table and paragraph-AI task records identified in the context.
- Source files listed in the context remain read-only to Hermes; Codex owns all edits and verification.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_aishuo_minimax` | `aishuo` | `MiniMax-M3` | `runs/conference/medical_writing_table_ai_revision_20260714/general_aishuo_minimax.md` |
| `general_buddy_deepseek` | `buddy` | `deepseek-v4-pro` | `runs/conference/medical_writing_table_ai_revision_20260714/general_buddy_deepseek.md` |
| `general_opencode_mimo` | `opencode-go` | `mimo-v2.5` | `runs/conference/medical_writing_table_ai_revision_20260714/general_opencode_mimo.md` |

## Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_chair_glm` | `buddy` | `glm-5.2` | `runs/conference/medical_writing_table_ai_revision_20260714/general_chair_glm.md` |

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- Record start/end time, session id, three-round continuity, pending/failed/incorporated status, retry reason and whether late outputs were used in metrics.

## Codex Verification Checklist

- Canonical table-cell anchor is server-derived and cross-project safe.
- Working-copy cell context is separated from original/evidence source claims.
- Submit/rewrite/apply all detect stale or changed cell state.
- Approved application updates top-level and structured cell representations, CAS version, snapshot and audit exactly once.
- Paragraph regression remains unchanged.
- RUX plus D001/PNH real-project matrix, Word preview and desktop browser pass.
