You are Hermes `buddy / kimi-k2.7-code` executing a bounded frontend implementation authorized by Codex.

Read and comply with `/Users/smkzw/.hermes/SOUL.md` fully.

Hard boundaries:
- Work only in the current workspace.
- You are not alone in the codebase. Backend source-admission hard-gate edits are concurrent; preserve them and do not revert unrelated changes.
- Do not open a browser or claim visual acceptance.
- Do not edit backend files.

Read:
- `frontend/AGENTS.md`
- `frontend/src/App.jsx`
- `frontend/src/styles.css`
- `tests/test_frontend_eligibility_contract.py`
- `reviews/codex_conference_monitoring_content_confirmation_ui_v1_review.md`
- `records/visual_qc_20260713/monitoring_content_confirmation/monitoring_content_confirmation_qc.json`

Authoritative API contract:
- On page/project change, POST `/api/projects/{routeProjectId}/eligibility/source-admission/refresh`.
- Response: `{ project_id, sources, missing_source_kinds, ready_for_use }`.
- Each source contains `entry` (`entry_id`, `source_kind`, `public_title`, `parser_status`, `size_bytes`, metadata) and `content_validation` (`revision`, technical/content/use status, checks, summary).
- Confirmation POST is the existing `/api/projects/{routeProjectId}/sources/{entryId}/content-validation/confirm` with exact warning/mismatch check codes, at least 10 chars reason, actor, expected revision and stable idempotency key.
- Confirmation preserves content_status warning/mismatch and changes use_status to confirmed_after_warning.
- Backend write/AI routes may return structured 409 `eligibility_source_confirmation_required`.

Write only:
- `frontend/src/App.jsx`
- `frontend/src/styles.css`
- `tests/test_frontend_eligibility_contract.py`

Requirements:
1. Add a desktop-first full-width `来源内容核验` band directly below the EligibilityPage title and before the status/workbench. Show separate `研究方案` and `受试者资料包` source rows/cards.
2. Show file basic information, technical status, content status, use status and every check. For raw subject bundle say explicitly: `目录及文件构成核验，不代表已完成逐文件医学内容核验`.
3. For each current warning/mismatch source, allow one source at a time to enter confirmation. Render one checkbox per unresolved check, empty reason, minimum 10 characters, clear warning that confirmation does not change mismatch/warning into match.
4. Confirm with exact codes and revision, then refresh admission. Show original content status and separate `已确认沿用`.
5. Reset confirmation form on project/source switch. Guard against stale async responses after project switching.
6. `ready_for_use` must be included in `canSaveMedicalDecision` and `canAcceptAiDraft`. Also disable other eligibility write actions that call `submitReviewAction`; read-only browsing, filters and visual QC remain available.
7. If a write action returns 409 with `detail.code=eligibility_source_confirmation_required`, refresh admission and show the source gate message. Preserve existing stale-review 409 behavior for other conflicts.
8. No security/malware scan wording, no local paths/hashes, no new route, no lifecycle numbering. Reuse existing 4px radius and confirmation visual tokens. No page horizontal overflow.
9. Add focused source-contract tests. Every newly disabled button must have title or aria-describedby.
10. Run focused tests and `npm run build` if feasible.

Return concise loop trace: files changed, behavior, tests, remaining uncertainty. Codex owns browser and final acceptance.

Write exactly one output file: `runs/conference/eligibility_source_admission_ui_v1/visual_buddy_kimi_implementation.md`.
