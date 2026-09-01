Same-session final visual follow-up. Codex accepted F1 and made only the
requested failed-state hierarchy correction.

Inspect:

- `evidence/mm_r7_slice07a_progress_ui_ego_acceptance_20260828/postfx_r5/failed_fullpage_r5_1920x1080_chrome_v2.png`
- the updated `postfx_r5/README.md` and
  `postfx_r5/ego_live_postfix_observations.json`
- current `frontend/src/features/medical-monitoring/r7/MedicalMonitoringR7ProgressPanel.css`

Changes are bounded to failed-state CSS: `本项未完成` is now a solid
risk-red 14px/30px badge with white text and shadow; failed numeric progress is
20px/700 dark red instead of the ordinary 24px/800 hero; the error track is
further muted. The new 1920 still is the pixel evidence. ego(lite) rechecked
the enlarged badge at 1280: no horizontal overflow, panel right edge 1250,
badge computed style is red background / white text / 14px / 30px.

The focused render contract now has 61 passing checks. Return the complete
role schema and rescore F1 only. Do not reopen withdrawn items or require an
ego PNG. Give `accept_limited` if F1 is closed; otherwise identify the exact
remaining visible pixel defect in the v2 still.
