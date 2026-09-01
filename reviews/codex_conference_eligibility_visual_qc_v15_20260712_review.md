# Codex Conference Review: eligibility_visual_qc_v15_20260712

Date: 2026-07-12

## Verdict

Pass for the bounded visual-QC workspace and processing-unit reconciliation slice. This is not eligibility-subsystem completion and does not authorize any bulk QC decision, VLM processing or medical eligibility conclusion.

## Boundary Compliance

- Exact Hermes route verified: `aishuo/MiniMax-M3`; three same-session rounds completed under session `20260712_043318_b2a3b5`, no fallback.
- No generated GLM, DeepSeek or Mimo role was dispatched; unused placeholders were deleted.
- Hermes read only the bounded source packet and did not inspect original clinical folders, OCR bodies, images or controlled artifacts.
- The first Hermes round described only lines 1-500 of SOUL.md as read; later same-session rounds and the postfix stated full read. Codex records this inconsistency and does not rely on Hermes for boundary authority.
- The final Hermes text incorrectly mentioned a Reasonix main reviewer although none was used in this conference. Codex rejected that process claim; it does not affect the source finding.

## Hermes Sub-Venue Review

- Initial review reproduced one valid P1: the image-content route could serve an immutable artifact whose source revision was no longer current.
- Codex added a current-source join and a stale-source rejection test.
- Hermes also requested route-level close/reopen coverage; Codex added a real FastAPI POST test proving pass closes and later fail reopens the unit.
- Same-session postfix re-read current source, accepted both fixes and found no remaining bounded P0/P1.
- The 100,000-character OCR limit remains intentionally fail-closed. Truncation was rejected because it could allow a user to pass an incomplete OCR representation.

## Main-Venue Codex Review

- Added controlled packet queue and image endpoints with project/subject/current-source binding, integrity verification, no-store/nosniff headers and sanitized errors.
- Added queue-wide status filtering/counts and bounded pagination.
- Added immutable QC-to-unit reconciliation: all evidence passed closes the unit; any later failed/manual result reopens it.
- Added stale frontend request fencing after Chrome reproduced an out-of-order filter response.
- Constrained result/reason combinations and added Chinese media-class labels.
- Preserved the explicit boundary that visual QC is not an IN/EX judgment or randomization release.

## Codex Independent Verification

- Real isolated runtime packet rebuild: 293/293 packets and corresponding images passed integrity readback without printing OCR text.
- Chrome read-only QC:
  - D001 SA07005: 35 evidence units.
  - MY009 S01009: 63 evidence units with 50+13 pagination.
  - 1600x1000 and 2048x1024: body width matched viewport; no page-level horizontal overflow or incoherent overlap.
  - 100% zoom produced internal image-pane scrolling only.
  - Rapid filter switching, reason/result coupling, return navigation and pagination passed.
  - Request log contained GET only; no real QC POST was submitted.
- Final backend regression: 602/602 passed in 205.49 seconds.
- Focused post-review tests: 24/24 passed; Ruff passed.
- Final frontend production build passed; existing >500 kB bundle warning remains.

## Final Decision

Accept this bounded slice. Retain the 1.2 GB controlled artifact set until real human QC and retention decisions are complete. All 293 real spans remain `needs_visual_qc/not_reviewed`; DOC/DOCX and archive units remain unresolved and continue to block independent AI review.
