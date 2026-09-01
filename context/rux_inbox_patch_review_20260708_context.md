# Task Context: rux_inbox_patch_review_20260708

Created: 2026-07-08 CST
Objective: Review the RUX-03-002 workbench inbox patch after Codex TDD implementation. Check logic, contract, source-boundary, regression, performance, and commercialization risks. Do not edit files.
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected Hermes route: `deepseek-v4-pro` / `high`

## Source Of Truth

Read these current workspace files only:

- `packages/contracts/workbench_contracts/models.py`
- `services/api/app/rux_monitoring_service.py`
- `services/api/app/workbench_inbox.py`
- `services/api/app/main.py`
- `tests/test_rux_monitoring_service.py`
- `tests/test_workbench_inbox.py`
- `research/rux_inbox_external_research_20260708.md`
- `reviews/codex_conference_rux_p0_backend_review_20260708_review.md`
- `metrics/rux_p0_backend_review_20260708_conference_metrics.md`
- `KNOWN_ISSUES.md`

Policy file allowed outside workspace:

- `/Users/smkzw/.hermes/SOUL.md`

## Implemented Change Summary

- Added `SubjectTimelineEventType.DOSE_ADJUSTMENT = "dose_adjustment"`.
- Changed RUX ECB `暂停用药` / `重新用药` timeline events from `protocol_deviation` to `dose_adjustment`.
- Added RUX project-aware workbench inbox support:
  - `RUX_PROJECT_ID = "proj_rux_03_002"`.
  - P0 subject anchors: `S01017`, `S01003`, `S03040`.
  - RUX inbox bypasses demo repository project validation only when `rux_monitoring_service` is injected.
  - RUX inbox item projection emits `WorkbenchItem` risk items with `target_page="monitoring"`, subject `target_id`, `status="待医学确认"`, and bounded P0 wording.
  - RUX source refs split listing row locators as `listing_data_row` and protocol anchors as `protocol_rule` with public `locator`.
  - For the RUX project, `_build_items()` returns only RUX monitoring projection in this P0 slice.
- Injected the existing `rux_monitoring_service` into `WorkbenchInboxService` from `main.py`.
- Added tests for dose-adjustment semantics and RUX inbox projection.
- Added external research note for current slice principles.

## Verification Already Run By Codex

- Baseline before patch:
  - `/api/projects/proj_rux_03_002/workbench-inbox?limit=20` returned `404` with `{"detail":"project not found: proj_rux_03_002"}`.
  - Two new target tests failed as expected:
    - ECB events were still `protocol_deviation`.
    - RUX workbench inbox returned 404.
- Focused green tests:
  - `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_rux_monitoring_service.RuxMonitoringServiceTests.test_subject_monitoring_links_lab_ae_and_dose_adjustment_chain tests.test_rux_monitoring_service.RuxMonitoringServiceTests.test_workbench_inbox_projects_verified_rux_monitoring_risks -v` -> 2 OK.
  - `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_rux_monitoring_service -v` -> 6 OK.
  - `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_workbench_inbox -v` -> 5 OK.
  - `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_contracts tests.test_rux_monitoring_service tests.test_workbench_inbox -v` -> 31 OK.
- API spot check:
  - RUX inbox: 200, 4 items, subjects `S01003`, `S01017`, `S03040`, no `/Users/`, no `protocol_deviation`.
  - Demo inbox: 200, no `/Users/`.
- Full backend regression:
  - `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v` -> 123 OK.

## Scope

In scope:

- Whether the RUX inbox implementation is logically safe and commercially defensible as a P0 slice.
- Whether source-boundary, source-locator, read-state, demo-regression, and contract risks are covered.
- Whether performance or architectural concerns should block this patch or be tracked as known issues.
- Whether test coverage is sufficient for this slice.

Out of scope:

- Frontend visual QA.
- Full 192-subject RUX monitoring coverage.
- Prohibited concomitant-medication semantic classification.
- Patient Profile chart implementation.
- Mutating original project files.
- Running commands, browsing, or editing files.

## Specific Questions For Hermes

1. Is the `RUX_PROJECT_ID` bypass in `WorkbenchInboxService` acceptable for P0, or does it create hidden cross-module risks?
2. Is returning only RUX monitoring items for `proj_rux_03_002` acceptable for this slice, given the current project is not in demo repository metadata?
3. Are `source_refs` typed and bounded enough for audit/source traceability?
4. Does `DOSE_ADJUSTMENT` introduce contract/frontend risks that should be addressed before continuing?
5. Are there source-boundary leaks or test gaps not covered by the listed verification?
6. Should any issue block the patch, or can Codex proceed with logging known limitations and next work?

## Risk Boundaries

- Do not approve this as a complete commercial RUX medical-monitoring system.
- Do not treat RUX P0 verified anchors as 192-subject coverage.
- Do not claim frontend/browser acceptance.
- Do not accept source locators if they expose local paths or hashes.
- Do not edit files.
