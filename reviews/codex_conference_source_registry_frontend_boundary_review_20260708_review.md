# Codex Conference Review: source_registry_frontend_boundary_review_20260708

Date: 2026-07-08 CST

## Verdict

Pass. Codex accepted the Hermes consensus and landed the scoped Source Registry frontend boundary patch with the agreed guards. No participant rerun required.

## Boundary Compliance

- Hermes ran advisory-only review. No Hermes model edited product source files.
- Codex retained final authority for patching, runtime tests, browser QC, and final acceptance.
- No non-medical lifecycle module or lifecycle-numbered subsystem was added.
- No clinical/regulatory final conclusion was delegated to Hermes.

## Participant Outputs Reviewed

- `runs/conference/source_registry_frontend_boundary_review_20260708/participant_qwen_plus.md`: recommended landing candidate-id UI flow, frontend source scan, and `处理中`.
- `runs/conference/source_registry_frontend_boundary_review_20260708/participant_mimo.md`: recommended landing, emphasized real frontend bundle path leak, `source_registry_qc.mjs` DOM guard, and title-vs-sourceLabel question.
- `runs/conference/source_registry_frontend_boundary_review_20260708/participant_ds_flash.md`: recommended landing, added structural guard/test coverage and deferral fallback.

## Hermes Sub-Venue Review

`runs/conference/source_registry_frontend_boundary_review_20260708/hermes_lead.md` synthesized all participant outputs. The chair found no substantive disagreement, recommended landing the patch, recommended using existing `title` instead of adding `sourceLabel`, and deferred backend config externalization to a tracked future task.

## Main-Venue DeepSeek Pro Review

`runs/conference/source_registry_frontend_boundary_review_20260708/main_deepseek_pro.md` passed the Hermes package and recommended landing after pre-landing checks. It required Codex to verify current source/dist path leak, candidate path existence and allowed-root coverage, full backend baseline, post-patch tests, frontend build, path scans, Source Registry QC, Safety/PV QC, TFL QC, and overview QC.

## Codex Independent Verification

Pre-landing:
- `rg -n "/Users/" frontend/src/App.jsx`: confirmed 12 frontend candidate path hits before patch.
- `npm run build && rg -n "/Users/" dist`: confirmed built bundle contained local absolute paths before patch.
- Candidate path precheck: 12/12 `SOURCE_REGISTRY_CANDIDATES` paths existed and were covered by configured allowed roots.
- Full backend baseline: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v` -> 114 OK.

Patch landed:
- Removed all frontend `sourceRegistryCandidates[*].path` local paths.
- Changed UI registration to `/sources/local-candidate?candidate_id=...&module=...`.
- Replaced candidate card path display with business title.
- Changed TFL and Safety/PV loading text from `提交中` to `处理中`.
- Added local-candidate endpoint tests and frontend source hygiene test.
- Added `leaksLocalPath` guard to `source_registry_qc.mjs`.
- Fixed QC runtime path/waiting issues encountered during verification.

Post-patch:
- Focused backend regression: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_source_registry tests.test_contracts -v` -> 33 OK.
- Full backend regression: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v` -> 116 OK.
- Frontend build: `npm run build` passed with known Vite chunk-size warning only.
- Path scans: `rg -n "/Users/" frontend/src/App.jsx frontend/dist frontend/src` -> zero hits.
- Local-candidate live probe: `ev-crs-trial-design` registered via candidate id; response excluded `/Users/`, `content_hash`, `preview_hash`, `storage_key`, and `server_path`.
- Browser QC passed:
  - `records/visual_qc_20260708/source_registry_boundary_patch/source_registry_qc.json`
  - `records/visual_qc_20260708/tfl_after_source_boundary_patch/tfl_manifest_qc.json`
  - `records/visual_qc_20260708/safety_after_source_boundary_patch/safety_pv_manifest_qc.json`
  - `records/visual_qc_20260708/overview_after_source_boundary_patch/overview_ai_gateway_qc.json`

## Final Decision

Accepted and closed for this patch. Deferred follow-up: externalize backend `SOURCE_REGISTRY_CANDIDATES` and `allowed_roots` before code distribution, multi-machine deployment, private-network deployment, or public repository push. The deferred item is recorded in `KNOWN_ISSUES.md` and `frontend/AGENTS.md`.
