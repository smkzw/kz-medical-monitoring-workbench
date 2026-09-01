# Codex Conference Review: medical_writing_editor_formatting_visual_20260714

Date: 2026-07-14

## Verdict

PASS WITH RECORDED KIMI EXCLUSION.

## Boundary Compliance

- Visual route remained Codex-led and had no Hermes chair.
- MiniMax-M3 and Qwen completed three rounds in the same session and did not write production code.
- Kimi timed out before a resumable session existed and is explicitly excluded; Qwen is the user-authorized fallback.
- Codex retained final browser, image, DOCX and production-write authority.

## Participant Outputs Reviewed

- MiniMax-M3: accepted the two-row, style-first, low-saturation active-state and structured-table-only principles. Its image tool failed, so screenshot claims were not used.
- Qwen: accepted the compact two-row ribbon and reduced table insertion path. Its runner output includes a diff transcript; only the recoverable final design recommendations were used.
- Kimi: no substantive output; excluded after terminal hard timeout.

## Hermes Sub-Venue Review

Not applicable. Visual/design conferences are no-chair panels under the workspace routing rules.

## Main-Venue Codex Review

The implementation keeps all user-requested Word-like controls visible in two 32 px rows instead of hiding superscript, subscript and colors in a generic overflow. At the measured 964 px editor width this remains readable and preserves immediate discoverability. The audit-oriented working-copy state bar was not collapsed into the AI action bar because version, save state, approval state and export actions have a separate governance meaning.

The table path remains explicit: current-table picker plus `插入表格`, followed by a six-field compact dialog and the existing full-screen structured table designer. The dialog fits without crowding at 1920x1080; hiding title, header rows, orientation or notes behind another disclosure would add clicks without resolving an observed density problem.

## Codex Independent Verification

- Browser regression passed on isolated runtime using real RUX-03-002, CMS-D001 and MY008211A-PNH-3-01 protocol sources.
- Measured at 2048x1024: toolbar height 80 px, two rows of 32 px, no viewport overflow, editor and AI rail visible.
- Additional 1920x1080 captures confirm the editor, AI rail, document map, custom-table dialog and full-screen 8x5 designer do not overlap.
- RUX saved/reloaded bold, underline, font, 14 pt size, red text, yellow highlight, superscript, subscript, justified alignment, 1.5 line spacing, first-line indent and paragraph spacing.
- D001 saved/reloaded Heading 3, Arial 12 pt, italic and left alignment.
- Draft DOCX inspection confirmed the same run/paragraph properties and a generated 8x5 landscape table; PNH exported 900 paragraphs and 24 tables without truncation.
- Focused suite passed: 83 tests. Frontend production build passed; only the existing large-chunk warning remains.
- A real RUX irregular DOCX table exposed ProseMirror filler-cell normalization. The parser now ignores only anonymous empty filler cells while still rejecting added content or identified cells.

## Final Decision

Accept the rich-editor slice for continued integration. Do not adopt the unobserved recommendation to hide explicit formatting controls or collapse audit state. Keep the Kimi failure and runner exception in the record, rerun that provider only when the runner/provider path is repaired, and rely on the completed MiniMax/Qwen perspectives plus Codex's direct evidence for this slice.
