# Codex Conference Review: workbench_resume_review_20260708

Date: 2026-07-08 CST

## Verdict

Status after DeepSeek Pro main-venue review: accepted for the current recovery slice; not a final product-completion decision.

Codex accepts the Hermes sub-venue consensus and DeepSeek Pro critique that the current overview recovery is acceptable as a short-term prototype fix. Codex also accepts DeepSeek Pro's escalation that duplicate inbox item ids should not be silently overwritten, and applied a deterministic duplicate-preservation suffix plus a regression test.

## Boundary Compliance

- Hermes participant prompts were preflighted by `hermes_workflow_guard.py` before dispatch.
- The participant and chair prompts allowed only specified workspace reads and one output file under `runs/conference/workbench_resume_review_20260708/`.
- The three participant models and Hermes lead reported no source-file edits, no web browsing, no browser/PPT/PDF/image acceptance, and no production-path reads.
- Codex remains final authority for code edits, tests, live API checks, browser QC, and final clinical/regulatory conclusions.

## Participant Outputs Reviewed

- `runs/conference/workbench_resume_review_20260708/participant_qwen_plus.md`
- `runs/conference/workbench_resume_review_20260708/participant_mimo.md`
- `runs/conference/workbench_resume_review_20260708/participant_ds_flash.md`

## Hermes Sub-Venue Review

Completed in `runs/conference/workbench_resume_review_20260708/hermes_lead.md`.

Sub-venue consensus:
- `SourceRegistrySpan.preview_hash` should receive model-level `exclude=True` as defense in depth.
- Remaining visible/default `EDC listing` wording should be harmonized to `原始数据 listing`.
- `_select_visible_items()` is acceptable as a recovery patch, but should be replaced later by production-grade grouping, filtering, subject-level aggregation, or type-aware pagination.
- All-phase 入排 scanning is correct for safety; do not revert to active-phase-only scanning.
- Module scope remains compliant: no first/fourth/fifth non-medical links and no lifecycle numbering in user-visible subsystem names.

Sub-venue disagreement preserved:
- Next build loop: qwen+ and ds_flash recommend 医学监查 RUX listing/protocol workflow first; mimo recommends 入排 D001 from-scratch workflow first. Codex has not made that next-loop decision in this review file.

## Main-Venue DeepSeek Pro Review

Completed in `runs/conference/workbench_resume_review_20260708/main_deepseek_pro.md`.

Main-venue decisions accepted by Codex:
- Run V1 live inbox type-diversity and V2 no-leak API checks before acceptance.
- Treat the eligibility router serialization path as a required read; Codex read `services/api/app/eligibility.py` and confirmed it returns `dataset.model_dump(mode="json")`, so model-level `exclude=True` fields are honored.
- Treat remaining EDC visible wording as an automated QC concern; Codex added `hasForbiddenEdcWording` to `frontend/tests/overview_ai_gateway_qc.mjs`.
- Promote `_dedupe_items` duplicate-id silent overwrite from deferred commercialization risk to current edit-round fix.
- Prefer 医学监查 RUX listing/protocol workflow as the next build loop, with 入排 D001 from-scratch workflow second; this remains a Codex recommendation, not a user-approved next action.

## Codex Independent Verification

Completed after final edit round:
- Focused backend tests: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_source_registry tests.test_workbench_inbox tests.test_eligibility_adapter tests.test_contracts -v` passed with 39 tests OK.
- Full backend regression: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v` passed with 114 tests OK.
- Frontend build: `npm run build` passed with only the known Vite chunk-size warning.
- Live API V1: `/api/projects/proj_mgk10_sar_demo/workbench-inbox?limit=80` returned 99 total open items, 80 visible items, and visible types including `source_ready`, `data_health`, `handoff`, `quality_gate`, and `picos_decision`.
- Live API V2: `/sources`, `/eligibility`, `/workbench-inbox`, and `/api/health` did not expose `/Users/`, `content_hash`, `preview_hash`, `storage_key`, `server_path`, `source_record_id`, or `data_path`.
- Browser QC: `APP_URL=http://127.0.0.1:5174/ API_URL=http://127.0.0.1:8910 QC_OUTPUT_DIR=records/visual_qc_20260708/overview_after_deepseek_review CHROME_DEBUG_PORT=9389 node frontend/tests/overview_ai_gateway_qc.mjs` passed.
- Final QC JSON: `records/visual_qc_20260708/overview_after_deepseek_review/overview_ai_gateway_qc.json`; desktop/mobile no horizontal overflow, 8 module rows, 10 visible inbox rows, 4 source-health rows, no lifecycle/non-medical/path/Source Registry/医学监督/EDC visible wording, unread count changed from 99 to 98 after click, total open count stayed 99.

## Final Decision

Closed for this recovery slice. Remaining work is product build continuation, not an unresolved review blocker:
- Replace `_select_visible_items` with production-grade grouping/filtering/pagination before commercialization scale.
- Consider explicit duplicate-id conflict telemetry or namespaced id contracts beyond the current deterministic suffix.
- Continue with 医学监查 RUX real listing/protocol workflow first unless the user reprioritizes.
- Preserve this closure in system/subsystem logs and create a soft-pause recovery note.
