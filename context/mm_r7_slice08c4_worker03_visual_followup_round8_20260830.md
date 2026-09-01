# 08C-4 worker_03 same-session visual remediation round 8

Continue the same bounded execution session. Read independent visual-conference Round 5 at `runs/conference/mm_r7_slice08c4_visual_acceptance_20260830/visual_single_object_round5.md`. Close all remaining P2-P4; do not seek waivers.

Required repair:

1. At 1280, the default table viewport must end after a complete column/header. No half-glyph `风` / `新`. Adjust responsive column widths/min-width/initial scroll geometry so the edge falls between columns. Keep all 11 columns reachable through the existing Chinese cue and linked in-card horizontal control.
2. Paint exactly one table rail/thumb. Hide the native scrollbar when the custom linked rail is active; confirm the custom control actually scrolls the table and has an accessible Chinese label. Do the same for Patient Journey: exactly one visible vertical rail/thumb, with the control linked to the real lane scroller.
3. Reduce excessive vertical whitespace in the phase-flow area and use responsive horizontal spacing so the four stages occupy the available width more naturally, especially at 1920. Bring the `高、中风险定位` and `查看受试者医学旅程` cards materially into the 1280/1440 first screen without crowding the required KPI+flow+table hierarchy.
4. Remove the adjacent `本次监查` / `日常监查` ambiguity using one concise native Chinese line that preserves cadence without repetition.
5. Keep the accepted study-status risk label, single site return, tamper suppression, aligned `由治疗进入研究状态`, first-token state, and drawer semantics unchanged.
6. Correct stale MANIFEST notes so they describe R8/current packet only.
7. Set structured clear false before capture. Re-run focused tests/build. Use ego(lite) native `captureScreenshot()` only to recapture 1280/1440/1920 overview, site, Journey and first-token (plus any other state affected). Rebuild matched Sankey/prototype and flow collages. Open originals and confirm one rail, whole edge headers, linked scroll behavior, visible lower cards, and responsive flow.
8. Start only 8984; stop it and complete all ego task spaces with `keep:false`.

No local Chromium, Playwright, Puppeteer, Chrome CLI, new dependencies, or new assets. Preserve medical-writing and unrelated work. Return exact residual P0-P4; do not claim Codex final acceptance.
