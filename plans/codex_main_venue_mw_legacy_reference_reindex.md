# Codex Main-Venue Plan: mw_legacy_reference_reindex

Date: 2026-07-15
Objective: 设计并审查医学写作导入方案中既有正文引文与参考文献的统一索引、重编号、编辑器绑定和DOCX导出闭环

## Task Decomposition

1. Inspect real imported RUX bibliography/body citation patterns and current rich-text/export contracts.
2. Define a versioned legacy-reference indexer that preserves raw strings, resolves only deterministic number-to-entry mappings, and records exceptions.
3. Project indexed legacy and new references into one ordered citation manifest and editor mark model.
4. Regenerate the reference section and DOCX hyperlinks/bookmarks from that manifest without mutating the immutable source.
5. Backfill RUX and PNH in isolated runtime, verify save/reload/export/XML, then promote after review.

## Source Packet

- User decision recorded in the conference context.
- Current exporter, project literature service, working-copy repository, contracts, editor and citation tests.
- Real RUX imported protocol reference-section observation: 19 numbered entries.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_aishuo_minimax` | `aishuo` | `MiniMax-M3` | `runs/conference/mw_legacy_reference_reindex/general_aishuo_minimax.md` |
| `general_opencode_deepseek_flash` | `opencode-go` | `deepseek-v4-flash` | `runs/conference/mw_legacy_reference_reindex/general_opencode_deepseek_flash.md` |

## Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_chair_grok45` | `grok-build` | `grok-4.5` | `runs/conference/mw_legacy_reference_reindex/general_chair_grok45.md` |

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- Initialized 2026-07-15 17:24 CST. One complete participant pass each; Codex decides whether targeted same-session follow-up is needed.

## Codex Verification Checklist

- No silent matching or source mutation.
- One index across legacy and new citations.
- Explicit ambiguity/orphan states and idempotent rollback/rebuild.
- XML proof for superscript hyperlinks, bookmarks and regenerated bibliography.
- Two real projects in isolated runtime before stable promotion.
