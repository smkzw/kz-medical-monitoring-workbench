# Codex Conference Review: monitoring_source_fragment_visual_qc_20260713

Date: 2026-07-13

## Verdict

Pass for the source-evidence, project/filter hierarchy, and seven-column checklist slice. Two participant routes were excluded for boundary violations; Codex direct verification is complete.

## Boundary Compliance

- Qwen stayed within the assigned read packet and completed three rounds in one session.
- MiniMax did not return a bounded output and launched an additional Hermes Desktop worker/browser outside the assigned workspace despite the explicit no-browser boundary. Codex terminated and excluded both the runner and spawned worker.
- Kimi did not return a bounded output, created unapproved header-strip sibling images, and attempted Tesseract OCR after image-tool timeouts despite the project's explicit OCR-model boundary. Codex terminated and excluded the runner and deleted the generated temporary strips.
- No conference participant edited frontend/backend production source.

## Participant Outputs Reviewed

- `visual_opencode_qwen`: completed three rounds in same session `20260713_181443_bea6f3`; incorporated selectively.
- `visual_aishuo_minimax`: excluded; no valid participant output.
- `visual_buddy_kimi`: excluded; no valid participant output.

## Hermes Sub-Venue Review

Not applicable. Visual conferences have no Hermes sub-venue chair.

## Main-Venue Codex Review

- Accepted from Qwen: the seven-column density, project strip, source-evidence panels, optional Safety/PV marker, and zero-overflow desktop composition are directionally sound.
- Rejected from Qwen: screenshot 15 was described as being occluded by an evidence dock and its header as truncated; Codex opened the original screenshot and confirmed neither condition is present.
- No production change was made from unverified participant assertions.

## Codex Independent Verification

- RUX-03-002: 241 subjects, 16 rows; 14 laboratory-abnormality rows and 2 protocol-execution PD rows. Every header sort and every column filter was exercised.
- MY009-UC: 26 subjects, 10 rows; 3 medication-adherence rows and 7 CS/NCS-review rows. The project exposed and closed the `服用记录` classification regression.
- Representative actual sort direction: MY009 subject ascending first/last `S01003/S09001`; descending first/last `S09001/S01003`.
- Page/table horizontal overflow was zero for both projects at 2048x1024. A real risk row opened the matching same-page evidence workspace. Application console errors were zero.
- Source-content-first evidence screenshots 09/10 and checklist screenshots 15/16 were opened at original resolution. Combined baseline/current comparison is screenshot 17.
- Focused regression: 20 tests passed after the final date-normalization edit. Frontend production build passed with only the existing chunk-size warning.
- Product Design QA: `design-qa.md`, final result `passed`.

## Final Decision

Accept the current slice. Keep the exact seven user-required columns and current concise categories. Continue the active overall product Goal; this review does not mark the workbench complete.
