You are OpenCode Go `qwen3.7-plus` finishing a bounded frontend implementation after Kimi reached its iteration limit.

Hard boundaries:
- Work only in the current workspace.
- You are not alone in the codebase. Preserve concurrent backend changes and unrelated user edits.
- Do not open a browser or claim visual acceptance.
- Do not edit backend files.

Read:
- `frontend/AGENTS.md`
- `frontend/src/App.jsx`
- `frontend/src/styles.css`
- `tests/test_frontend_eligibility_contract.py`
- `prompts/conference/eligibility_source_admission_ui_v1/visual_buddy_kimi_implementation.md`
- `runs/conference/eligibility_source_admission_ui_v1/visual_buddy_kimi_implementation.md`
- `reviews/codex_conference_monitoring_content_confirmation_ui_v1_review.md`

Kimi partially edited `EligibilityPage` but did not finish. Current known defects:
- `SourceAdmissionBand` is referenced but not defined.
- styles and focused tests are absent.
- `submitAdmissionConfirmation` sets `admissionConfirmedRecord` then `resetSourceAdmissionForm()` clears it immediately.
- one error message says `确认溯用`; use `确认沿用` everywhere.
- the visual band currently appears after status/boundary; requirement is directly below the title and before eligibility status.

Authoritative API and behavior:
- POST `/api/projects/{routeProjectId}/eligibility/source-admission/refresh` -> `{ project_id, sources, missing_source_kinds, ready_for_use }`.
- Confirm at `/api/projects/{routeProjectId}/sources/{entryId}/content-validation/confirm` with exact unresolved codes, >=10-char reason, expected revision and stable idempotency key.
- Confirmation preserves content_status warning/mismatch and changes only use_status to confirmed_after_warning.
- Show research protocol and raw subject bundle separately. Bundle copy must say `目录及文件构成核验，不代表已完成逐文件医学内容核验`.
- Show technical/content/use status and all checks. One active confirmation form at a time.
- Empty reason, checkbox each warning/mismatch, disabled confirm until all selected and >=10 chars.
- `ready_for_use` disables every eligibility write action that calls `submitReviewAction`, but does not block read-only browsing, filters or visual QC.
- Structured 409 `eligibility_source_confirmation_required` refreshes the source gate; other 409 stays stale-review conflict.
- No malware/security-scan copy, paths, hashes, lifecycle numbering, or new routes.
- Desktop-first, existing 4px tokens, no page overflow.
- Every disabled button needs title or aria-describedby.

Write only:
- `frontend/src/App.jsx`
- `frontend/src/styles.css`
- `tests/test_frontend_eligibility_contract.py`

Run focused eligibility/button tests and `npm run build` if feasible. Return a concise loop trace and write exactly one output file:
`runs/conference/eligibility_source_admission_ui_v1/visual_opencode_qwen_fallback.md`.
