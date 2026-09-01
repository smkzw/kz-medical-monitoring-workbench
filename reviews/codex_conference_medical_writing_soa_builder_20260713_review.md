# Codex Conference Review: medical_writing_soa_builder_20260713

Date: 2026-07-13

## Verdict

Pass with bounded revisions. The conference supports a generic structured-table engine with a Schedule of Activities (SoA) domain layer, but several proposals were intentionally narrowed after Codex implementation and real-project checks.

## Boundary Compliance

- All four roles completed three rounds in the same recorded session.
- Participants remained read-only and did not claim final browser, Word, clinical, or production acceptance.
- `glm-5.2` chaired the logic-heavy conference. The visual-QC route remains `MiniMax-M3`, `kimi-k2.7-code`, and `qwen3.7-plus`; no Reasonix second review is permitted.
- Trailing Hermes MCP event-loop cleanup warnings occurred after successful output persistence. They did not truncate the substantive reports, but are retained as runner evidence.

## Participant Outputs Reviewed

- `MiniMax-M3`: proposed a minimal stable grid, first-class notes, and a hybrid inline/document plus full-screen matrix editor.
- `deepseek-v4-pro`: proposed a generic table model, SoA domain plugin, synchronized rendering, and review/audit boundaries.
- `mimo-v2.5`: emphasized typed structures, merge-aware parsing, atomic batch updates, stable note references, and deterministic Word export.
- `glm-5.2`: compared the participants, challenged concurrency and parser failure behavior, and converged on generic grid plus SoA validation.

## Main-Venue Codex Review

Accepted:

- One canonical structured-table model shared by inline editor, full-screen designer, version history, notes, and Word export.
- Stable table, row, column, cell, and note IDs; `gridSpan`/`vMerge` preservation; optimistic compare-and-swap updates.
- SoA as the first dedicated domain designer, with study periods, visits, study days, visit windows, activities, execution states, and structured notes.
- Graduated import outcomes: structurally valid, warning/review required, or blocked when the grid cannot be represented without data loss.
- Inline real-table rendering for every protocol table; complex tables open the full-screen designer without creating a second document or version chain.

Revised or rejected:

- Rejected the suggestion that TipTap should be read-only. The user requires direct table editing in the document working copy.
- Rejected byte-identical source-DOCX round-trip as an acceptance criterion. Semantic structure, ordered content, visual layout, and traceability are required; OOXML packages may normalize while remaining equivalent.
- Deferred a separate `TableRevision` persistence entity. Current working-copy snapshots plus table version/CAS provide the required audit boundary without duplicating the document revision chain.
- Rejected adding AG Grid/Handsontable at this stage. The custom desktop grid handles the verified 34x11 and 42x19 cases without a new license or framework boundary; performance will be re-evaluated against wider real tables.
- Rejected fail-fast for every imperfect import. Recoverable ambiguity must remain visible for human confirmation rather than making a readable source unusable.

## Codex Independent Verification

- Parser checks on real RUX, D001, and PNH DOCX files preserved unique stable IDs and merge continuations without grid overflow.
- API/service tests covered table retrieval, cell and structural edits, CAS conflict, idempotent replay, persistence, and DOCX round-trip.
- Browser QC at 2048x1024 verified the real RUX 34x11 SoA, four structural header rows, correct merged study-period cells, dense scrolling, inline-table synchronization, merge/split, row/column operations, notes, and orphan-note protection.
- Current evidence image: `records/active_slices/medical_writing_soa_builder_20260713/02_rux_soa_designer_2048x1024.png`.

## Final Decision

Proceed with the implemented architecture. The remaining production work is whole-document Word export, source caption/note association, reusable non-SoA table templates, six-study regression, and approved-snapshot export gating. Codex retains final acceptance authority.
