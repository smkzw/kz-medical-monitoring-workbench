# Codex Conference Review: medical_writing_visible_table_editor_20260714

Date: 2026-07-14

## Verdict

Pass after revision. The visible-table slice meets the requested desktop writing workflow: all protocol tables render as synchronized editable tables, no raw Markdown/omission fallback remains, and complex wide tables expose explicit horizontal navigation.

## Boundary Compliance

- The visual conference used the required no-chair panel: aishuo/MiniMax-M3, buddy/kimi-k2.7-code and opencode-go/qwen3.7-plus.
- Each participant completed three rounds in one resumable session with no fallback and no production write.
- MiniMax and Kimi disclosed image-tool timeouts. Qwen and Codex supplied the useful visual findings; Codex retained final screenshot/browser authority.
- Kimi read a transient one-project QC report while the three-project report was being regenerated. Its blocking parity conclusion is superseded by the final zero-failure three-project report and is not accepted.

## Participant Outputs Reviewed

- MiniMax-M3: correctly identified the wide-table and long-note discoverability risks, but its sticky-header and gradient recommendations were source/pixel inference rather than live browser proof.
- kimi-k2.7-code: usefully challenged scroll synchronization and density, but the floating sync-overlay, IntersectionObserver rewrite and one-project parity blocker were disproportionate or stale for this slice.
- qwen3.7-plus: corrected its own false whole-table AI-context claim and provided the most directly useful finding: native horizontal scrolling alone was insufficiently discoverable.

## Hermes Sub-Venue Review

Not applicable. Visual conferences are Codex-led and have no Hermes sub-venue chair.

## Main-Venue Codex Review

Accepted:

- Add left/right icon controls only when the active table horizontally overflows.
- Keep the real table, actual title, source title when different, dimensions, complete note content and note count in the editor-first surface.
- Preserve one structured-table object across inline editing, full-screen design, AI cell revision, persistence and Word export.

Rejected or deferred:

- Do not convert the sync band to a floating overlay or hide it; that would weaken source/table context during medical review.
- Do not reverse Chinese select text direction or enlarge the notes pane by default; both reduce predictable desktop scanning space.
- Do not add sticky headers until the nested horizontal/vertical scroll ownership is redesigned and proven across merged tables.
- Do not replace the bounded rAF scroll observer with IntersectionObserver without measured performance evidence; the current 68-table real-project run showed no functional failure.

## Codex Independent Verification

- Original-resolution 1600x1000 screenshots for RUX-03-002, CMS-D001 and MY008211A-PNH-3-01 were inspected after the final change.
- Chrome API-to-DOM QC passed 3 projects, 42 table-bearing sections, 68 tables, 3,748 visible cells and 146 notes with zero failures.
- QC checks cover table title/source caption, row/column and note counts, exact cell text and hard breaks, picker/block identity, vertical linkage, horizontal-control action, dirty-state regression, placeholder text and Markdown separators.
- A real same-section multi-table race was reproduced in RUX: smooth scrolling could let the visible-table observer overwrite the user-selected table. A 500 ms stable-block guard plus immediate scroll fixed the race; the full three-project rerun passed.
- Full repository regression: 880 passed, 12 existing dependency warnings. Backend compile, QC-script syntax and frontend production build passed. The existing Vite >500 kB chunk warning remains.

## Final Decision

Approve this slice. The remaining sticky-header, note-expansion and observer-performance ideas belong to later measured ergonomics/performance work; they do not block the user's requested synchronized table review and modification workflow.
