# 08C-4 worker_03 same-session ego-only recapture round 6

Continue the same bounded execution session. Round 5 product changes may remain, but its visual evidence is not admissible because it fell back to local Chromium after an ego(lite) CDP timeout. The user explicitly requires ego(lite), and the frozen visual contract requires ego-only evidence.

Do not use local Chromium, Playwright, Puppeteer, Chrome CLI, or any browser other than ego(lite). Do not claim `p0_to_p4_clear=true` until an ego-only packet exists.

Required work:

1. Immediately set FINDINGS/MANIFEST structured clear to false and label the Round 5 Chromium PNGs non-authoritative or superseded without deleting them.
2. Diagnose the ego screenshot timeout inside the existing allowed task scope. Use ego's native `captureScreenshot()` helper first. If a fixed drawer is lost after scroll, navigate directly to the required state/anchor at page top, use an ego fresh tab/task space, reduce capture scope to the viewport, wait for stable paint, or use bounded ego CDP retries. A CDP timeout is not permission to change browsers.
3. Recapture every Round 5 affected original exclusively through ego(lite): 1280/1440/1920 overview, site, Journey, tamper, plus any drawer/overlay state whose source image was overwritten by Chromium. Preserve exact viewport dimensions, including 1920x1080.
4. Rebuild the structured JSON and collages from those ego captures, including `overview_flow_strip`, `site_flow_strip`, `1280_overview_side_by_side`, and `1280_overview_vs_sankey_ref.png` so reference and current prototype are in one comparison image.
5. Open the new ego originals and comparison collages. Confirm: complete table headers/no orphan wrap; visible table-local scroll affordance if used; no page overflow; no connector badge collision; one site return; clean inspector meta; visible Journey axis scroll affordance; no tamper delta labels; consistent `数据完整性`.
6. Re-run focused tests/build only if capture-related edits are needed. Start only 8984, then stop it and complete all ego task spaces with `keep:false`.
7. Record the exact ego capture method, task-space id(s), PNG mtimes, and any retries in the report and manifest. Only then may structured clear return to true. Do not claim Codex final acceptance.

No new dependencies/assets. Preserve medical-writing and unrelated work.
