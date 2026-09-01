# Codex Conference Review: rux_monitoring_inbox_detail_20260708

Date: 2026-07-08 CST

## Verdict

Pass for this bounded RUX 医学监查 inbox/detail migration slice.

This is not a pass for full 192-subject RUX medical monitoring commercialization. It accepts only the verified P0 behavior: RUX 医学监查 risk list/detail now uses real `workbench-inbox` risk items, supports real-subject drilldown, and persists a safe `mark_read` action.

## Boundary Compliance

- Original RUX project files under `/Users/smkzw/Documents/康哲项目资料` were treated as read-only.
- The slice uses real `proj_rux_03_002` workbench inbox items derived from RUX listing/protocol services; it does not reuse MG-K10/demo Subject Timeline HTML as the risk engine.
- Public UI/QC checks verified no demo/internal leakage in the RUX monitoring page: no MG-K10 demo subjects, no technical batch id, no local path/hash/storage fields.
- Unsupported risk dispositions were not exposed in the RUX detail action area. The only wired action is `mark_read`; Query, close, and formal disposition remain deferred until a real risk-disposition workflow exists.
- The slice preserves the P0 boundary wording: current RUX inbox displays verified medical-monitoring risk anchors only and is not full-project medical monitoring coverage.

## Participant Outputs Reviewed

- `runs/conference/rux_monitoring_inbox_detail_20260708/participant_qwen_plus.md`: accepted as advisory. It identified the core gap that `MonitoringPage` ignored `workbenchInbox`, mixed demo rows, and had inert action buttons.
- `runs/conference/rux_monitoring_inbox_detail_20260708/participant_mimo.md`: accepted as advisory. It independently confirmed the same data-flow gap, emphasized `mark_read` state refresh, and recommended source-ref display without local path leakage.
- `runs/conference/rux_monitoring_inbox_detail_20260708/participant_ds_flash.md`: accepted as advisory. It independently confirmed backend `mark_read` as the only safe action and pushed for browser/QC coverage of real subjects and action persistence.

## Hermes Sub-Venue Review

`runs/conference/rux_monitoring_inbox_detail_20260708/hermes_lead.md` was reviewed. The Hermes lead found no substantive participant conflict and synthesized the correct implementation contract:

- use real inbox items when available;
- preserve demo fallback only when real inbox items are absent;
- map `target_id` to the selected real subject;
- display source refs as reader-facing evidence, not raw paths;
- wire only `mark_read`;
- verify with static contract tests and desktop/mobile browser QC.

No rerun was required.

## Main-Venue DeepSeek Pro Review

`runs/conference/rux_monitoring_inbox_detail_20260708/main_deepseek_pro.md` was produced through the DeepSeek supplier `deepseek-v4-pro` route. It issued a conditional pass and required Codex to personally verify the implementation files and live checks.

Codex performed the requested checks after the review:

- `frontend/src/App.jsx` contains `monitoringRiskRowsFromInbox(workbenchInbox)` and `MonitoringPage(... workbenchInbox, refreshWorkbenchInbox)`.
- `visibleRiskRows` is conditional: generated upload risks first, then real inbox risks, then demo fallback. It no longer unconditionally concatenates `generatedRiskRows` and `riskRows`.
- RUX inbox row mapping uses `item.target_id` for `risk.subject`; clicking a risk row calls `setSelectedRiskId(risk.id)` and `setSelectedSubject(risk.subject)`.
- `RiskDetail` exposes source refs through `sourceRefTypeLabel(...)` and `compactLabel(...)`, capped at six source chips.
- `RiskDetail` does not contain the unsupported `接受不处理` or `提交复核` actions; it shows only the safe `标记已读` action when available.

## Codex Independent Verification

Focused and live checks:

- `python3 -m unittest tests.test_frontend_monitoring_contract -v`: 4 OK.
- `npm run build` in `frontend/`: passed with the known Vite chunk-size warning only.
- `APP_URL=http://127.0.0.1:5176/ API_BASE=http://127.0.0.1:8920 QC_OUTPUT_DIR=.../records/visual_qc_20260708/rux_monitoring_inbox CHROME_DEBUG_PORT=9377 node frontend/tests/rux_monitoring_inbox_qc.mjs`: passed.
- Full regression from the same continuation: `python3 -m unittest discover -s tests -v`: 141 OK.

Browser/QC evidence:

- Metrics file: `records/visual_qc_20260708/rux_monitoring_inbox/rux_monitoring_inbox_metrics.json`.
- Desktop and mobile both rendered 4 real RUX risks.
- Risk list contained real RUX subjects `S01003`, `S01017`, and `S03040`.
- Target detail `S01017 ALT/AST >5xULN` rendered with RUX P0 boundary note, listing source ref, protocol source ref, and readable batch label.
- No demo/internal text leak was detected by the QC guard.
- No horizontal overflow was detected in monitoring detail, Subject Timeline handoff, or Patient Profile handoff.
- `mark_read` changed unread count from 4 to 3, preserved total open count at 4, kept the item in the inbox, and returned the item as `unread=false`.
- Subject Timeline handoff for `S01017` showed the subject, lab lane, and ALT/AST content.
- Patient Profile handoff for `S01017` showed the subject and all core efficacy/safety trend cards.

## Final Decision

Accept this slice as implemented and verified.

Remaining product gaps after this acceptance:

- This remains a P0 risk-anchor workflow, not full 192-subject RUX monitoring.
- `mark_read` is the only supported inbox action; formal risk disposition, Query workflow, close/reopen, and audit-classification actions need a later workflow.
- RUX full-subject/incremental batch parsing and refreshed-listing stable identifiers remain future commercialization work.
- Patient Profile mobile subject-tree density remains a UX refinement item.
