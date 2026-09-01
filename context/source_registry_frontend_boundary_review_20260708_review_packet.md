# Review Packet: Source Registry Frontend Boundary Review

Created: 2026-07-08 CST

## User Instruction Being Served

The user asked Codex to let Hermes review previous Codex work in the background, provide enough information for Hermes to judge properly, discuss Hermes recommendations with Codex, and only land changes that both Hermes and Codex accept.

## Current Scope Boundary

- This is the AI medical manager workbench.
- User-facing modules must remain medical/business modules only: `项目总看板`, `证据调研与方案设计`, `入排审核`, `医学监查`, `数据分析与TFL`, `医学写作`, `安全信号与PV协同`, `审批中心`.
- Do not expose non-medical clinical-development links 1/4/5.
- Do not render lifecycle numbering such as `第几环节`, `阶段`, or `Stage` in subsystem names.
- Hermes must not edit code in this review. This pass is advisory only.

## Current Code Facts From Codex Inspection

Codex ran:

```bash
rg -n "/Users/|candidate\.path|file_path|root_path|local-candidate|sourceLabel|提交中" frontend/src/App.jsx services/api/app/main.py tests || true
```

Relevant observations:

- `services/api/app/main.py` now contains `SOURCE_REGISTRY_CANDIDATES` with server-side mappings from candidate ids to local paths.
- `services/api/app/main.py` now contains `POST /api/projects/{project_id}/sources/local-candidate`.
- `frontend/src/App.jsx` still contains local absolute paths inside `sourceRegistryCandidates`.
- `frontend/src/App.jsx` still submits `file_path` / `root_path` from `candidate.path` to `/sources/local-file` or `/sources/local-directory`.
- `frontend/src/App.jsx` still renders `shortPath(candidate.path)` in source candidate cards.
- `frontend/src/App.jsx` still uses loading button text `提交中` in TFL and Safety/PV review actions; a previous Safety/PV QC script can treat that as a forbidden PV-overclaim button because it matches the broad forbidden pattern `/提交|批准PV|启动|写入|最终判定|生成E2B/`.

## Prior Verification Baseline

Recent records in `logs/system_build_log.md` show:

- Focused public-boundary tests previously passed for Source Registry, unified inbox, eligibility, and contracts.
- Full backend regression previously passed: `python3 -m unittest discover -s tests -v` with 114 OK.
- Frontend production build previously passed with only the known Vite chunk-size warning.
- Overview browser QC previously passed desktop/mobile.
- Source Registry API responses were checked not to expose `/Users/`, `content_hash`, `preview_hash`, `storage_key`, `server_path`, `source_record_id`, or `data_path`.

This baseline does not close the current frontend bundle issue, because the frontend source and built bundle can still contain local absolute paths even when the visible UI and API payloads do not show them.

## Proposed Codex Fix To Review

Codex proposes the following scoped patch, but must not land it until Hermes/Codex consensus is reached:

1. Keep server-side `SOURCE_REGISTRY_CANDIDATES` as an internal allowlisted mapping.
2. Update frontend `sourceRegistryCandidates` so each candidate contains only:
   - `id`
   - `title`
   - `kind`
   - `module`
   - `sourceKind` when needed
   - `sourceType`
   - `purpose`
   - a non-sensitive display label such as `sourceLabel`
3. Update frontend `registerCandidate()` to call:
   - `POST /api/projects/{project_id}/sources/local-candidate?candidate_id=...&module=...`
   - no `file_path`
   - no `root_path`
4. Update candidate card display to show `sourceLabel` or `id`, not `shortPath(candidate.path)`.
5. Change review-action loading text from `提交中` to a neutral term such as `处理中`.
6. Add tests/guards:
   - API test for `/sources/local-candidate` success, module mismatch, unknown candidate, and public payload non-leak.
   - frontend source/bundle scan asserting `frontend/src/App.jsx` and `frontend/dist` do not contain `/Users/`.
   - update browser QC if needed so Source Registry registration still works.

## Questions For Hermes

1. Is the server-side candidate-id mapping approach the correct product boundary for local single-machine now and future private-network deployment?
2. Is it acceptable for backend source code to contain local absolute paths as internal allowlisted mappings, provided API and frontend bundles do not expose them? If not, what minimal configuration layer should replace it now?
3. Should the legacy `/sources/local-file` and `/sources/local-directory` endpoints remain for internal/developer use, or should UI-facing flows only use `/sources/local-candidate`?
4. Are the proposed tests sufficient to prevent recurrence, or is another contract/browser guard needed?
5. Is changing `提交中` to `处理中` the right UI-level fix for the Safety/PV QC false positive and clinical/PV boundary wording?
6. Does this scoped patch conflict with the user's instruction to soft pause after preserving logs, or is it a necessary non-lossless completion because the backend fix is already partially present?

## Expected Output From Hermes

- State what files were read.
- Separate evidence, inference, recommendation, and uncertainty.
- Do not claim browser/visual/final product acceptance.
- Provide a clear recommendation: land, revise then land, defer, or rerun.
- If recommending land, list exact required verification commands.
- If recommending defer, list the risk of leaving the current partial backend/frontend mismatch in place.

