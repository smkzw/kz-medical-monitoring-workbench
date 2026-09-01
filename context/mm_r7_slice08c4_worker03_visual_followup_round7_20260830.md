# 08C-4 worker_03 same-session visual remediation round 7

Continue the same bounded execution session. Read independent visual-conference Round 4 at `runs/conference/mm_r7_slice08c4_visual_acceptance_20260830/visual_single_object_round4.md` and close its remaining P2-P4 without changing architecture or adding dependencies.

Decisions for this bounded repair:

- All 11 homologous-table columns remain available. At 1280/1440, a contained horizontal scroll is acceptable only with a persistently painted, high-discoverability table-local rail/thumb visible in the default ego screenshot. Do not rely on macOS overlay scrollbars or hover. No page-level overflow.
- `中高风险 1` below the study-status node with a clear gap is accepted; do not regress it.
- P3/P4 must also be zero; do not ask Codex to waive them.

Required work:

1. Add a persistent painted table-local horizontal scroll affordance at 1280/1440. Prefer native scroll container styling that remains visible in ego; if the OS still suppresses it, add an accessible, linked in-card scroll control using existing components/icons and Chinese-native text such as `左右滑动查看完整明细`, without hiding columns or creating a page scrollbar. The default still must visibly communicate that `数据完整性` and `医学旅程` are available to the right.
2. Make the Patient Journey axis-local vertical scroll rail/thumb persistently visible at 1280/1440 when MH and later lanes extend below the fold. Do not merely set `overflow-y: scroll`.
3. Recapture the first-token overview in ego so `路径完整 1` is absent from authoritative evidence.
4. Align the homologous row `关键原因` with the actual transition `治疗 → 研究状态`; use concise medical-monitor wording.
5. Refresh the evidence-pack MANIFEST mtimes/gates so it points to the current files and agrees with FINDINGS.
6. Before capture set structured clear false. Using ego(lite) native `captureScreenshot()` only, recapture 1280/1440 overview, site, Journey, first-token and any 1920 state affected; rebuild the matched reference/prototype and flow collages. Open the original PNGs and verify the rails/thumbs are actually painted.
7. Re-run focused tests/build if source changes. Start only 8984, then stop it and complete all ego task spaces with `keep:false`. Record exact task-space id and capture method.

Do not use local Chromium, Playwright, Puppeteer, Chrome CLI, or another browser. No new assets/dependencies. Preserve medical-writing and unrelated work. Return exact residual P0-P4; do not claim Codex final acceptance.
