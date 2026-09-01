You are Hermes `buddy / kimi-k2.7-code` executing a bounded frontend implementation authorized by Codex.

First read and comply with `/Users/smkzw/.hermes/SOUL.md` fully.

Hard boundaries:
- Work only in the current workspace.
- You are not alone in the codebase. Preserve concurrent backend changes and do not revert unrelated edits.
- Do not read files outside the explicit read list.
- Do not modify files outside the explicit write list.
- Do not open a browser or claim visual acceptance.

Read these files only:
- `context/monitoring_content_confirmation_ui_v1_conference_context.md`
- `runs/conference/monitoring_content_confirmation_ui_v1/visual_buddy_kimi.md`
- `runs/conference/monitoring_content_confirmation_ui_v1/visual_aishuo_minimax.md`
- `runs/conference/monitoring_content_confirmation_ui_v1/visual_opencode_qwen.md`
- `frontend/AGENTS.md`
- `frontend/src/App.jsx`
- `frontend/src/styles.css`
- `frontend/src/features/writing-reference/WritingReferencePanel.jsx`
- `tests/test_frontend_monitoring_contract.py`
- `frontend/tests/monitoring_upload_qc.mjs`

Backend contract already implemented and authoritative:
- First file upload may return HTTP 409 with `detail.code=source_content_confirmation_required`, `detail.source_entry_id`, and `detail.validation`.
- Confirmation POST: `/api/projects/{projectId}/sources/{sourceEntryId}/content-validation/confirm` with `reason`, exact `acknowledged_check_codes`, `actor`, `expected_revision`, and `idempotency_key`.
- Confirmation success keeps `content_status=warning|mismatch` and changes only `use_status=confirmed_after_warning`.
- After confirmation, retry the same `/monitoring/intake/file` request exactly once with the original File object.

Write exactly these source files if changes are required:
- `frontend/src/App.jsx`
- `frontend/src/styles.css`
- focused frontend contract or browser test files only if needed.

Requirements:
1. In `MonitoringPage`, preserve the original File object for CSV as well as XLS/XLSX/XLSM; CSV parsing remains preview-only.
2. Intercept the structured 409 and render an inline full-width confirmation area inside the existing `.upload-grid`, after the three existing columns.
3. Show all checks with outcome labels; unresolved warning/mismatch checks each have one checkbox.
4. Empty-by-default reason, minimum 10 characters. Confirm button disabled until all current unresolved codes are selected.
5. Confirmation calls the confirmation endpoint then retries the original file upload once. Secondary retry failure must keep the confirmed record visible and explain that confirmation was recorded but rule execution failed.
6. Switching file or closing upload gate clears old confirmation state. Do not leak hashes or local paths.
7. Display content status unchanged and a separate `已确认沿用` state; never relabel mismatch as match.
8. Reuse existing visual tokens and 4px radius. Desktop-first, no page horizontal overflow. Avoid new route/page and avoid security-scan language.
9. Do not modify the monitoring risk ledger, Subject Timeline, Patient Profile, backend, or medical-writing component.
10. Run focused tests and `npm run build` from `frontend` if feasible.

Return a concise loop trace: files changed, behavior implemented, tests run, remaining uncertainty. Do not claim browser acceptance; Codex owns it.

Write exactly one output file: `runs/conference/monitoring_content_confirmation_ui_v1/visual_buddy_kimi_implementation.md`. The bounded runner persists your final response there.
