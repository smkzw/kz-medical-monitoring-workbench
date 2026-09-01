# Codex Conference Review: safety_pv_visual_acceptance_20260714

Date: 2026-07-14

## Verdict

Pass after Codex verification. No production UI change is justified by the panel findings. The browser-QC contract was strengthened to turn the disputed visual claims into deterministic DOM assertions.

## Boundary Compliance

- Visual/design conference used the required no-chair panel: aishuo/MiniMax-M3, buddy/kimi-k2.7-code and OpenCode Go/qwen3.7-plus.
- Each participant completed three rounds in one session. Kimi round 2 exited during MCP cleanup, then resumed the same session and completed round 3.
- Participants were advisory only and did not edit production source. Codex retained final screenshot, DOM, browser and production-write authority.
- The fixed product boundaries remained unchanged: seven-column Checklist, same-page evidence dock, source facts before folded locators, no second PV risk ledger and desktop-first layout.

## Participant Outputs Reviewed

- MiniMax raised apparent cross-project differences in dock tabs and document columns, plus canvas and dock-density concerns.
- Kimi raised dock occlusion, disabled-action explanation, document-header, center-ID and audit-density concerns.
- Qwen retracted earlier fabricated observations and retained only dock placement, page scrolling and all-high-risk-data observations.

## Hermes Sub-Venue Review

Not applicable. This was a Codex-led visual panel with no Hermes chair.

## Main-Venue Codex Review

The panel was useful as an adversarial prompt, but several high-severity findings were caused by screenshot scaling or by treating a scrolled capture as a missing component:

- MY009 visibly contains all six dock tabs in the required order; MiniMax's five-tab claim was false.
- Both projects render three document-review columns with five candidate buttons. The MY009 screenshot was captured after the selected action had been scrolled into view; the empty visible area did not mean the candidate rail was absent.
- The reported empty right half came from reading a roughly 960-pixel model representation as if its coordinates were the original 1920-pixel screenshot.
- RUX center IDs are already zero-padded, risk-category tags are not clipped, disabled action buttons already carry state-specific titles, and the medical-opinion field is separately labelled.
- An internal dock scrollbar is intentional for a resizable same-page evidence workspace and is not a defect by itself. Replacing it with page scroll would weaken context retention.

No panel finding met the production-edit threshold after direct image and DOM verification.

## Codex Independent Verification

- Direct original-resolution inspection covered all six PNG files at 2048x1024 and 1920x1080.
- The Google Chrome/CDP script was extended with `riskEvidenceMetrics.tabs`, dock geometry, candidate count, document-grid child count and per-column widths.
- Re-run results for both RUX-03-002 and MY009-UC: six tabs in exact order; dock width 1320; five candidate buttons; three review-grid children; grid width 1637; child widths 428/723/463; no result failures, console errors, failed responses, clipping, overlap, horizontal overflow, local-path leak or lifecycle number.
- The dual-project browser script again completed all five Safety/PV review actions and reset both isolated projects to `待医学/PV确认`.
- Full repository regression passed: `910 passed, 12 warnings` in 547.75 seconds. Frontend production build passed earlier in the same slice.
- Main runtime was backed up, migrated to SQLite schema 16 and cold-restarted; health reports integrity `ok`, zero foreign-key violations and zero audit-chain violations.

## Final Decision

Accept the current Safety/PV visual implementation for this slice. Retain the new deterministic visual-QC fields so future cross-project regressions fail in the browser test instead of being inferred from screenshot scaling. Do not implement the panel's proposed extra compare panel, second dock mode, per-button captions, row animation or locator count badge in this slice.
