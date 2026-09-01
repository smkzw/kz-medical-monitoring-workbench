# Codex Conference Review: prior_work_rux_preflight_review_20260708

Date: 2026-07-08 CST

## Verdict

Final status for this advisory review: Hermes sub-venue + DeepSeek Pro main-venue review completed and are accepted as planning/preflight evidence. No product-code change was landed from this review because the only proposed "land now" code change was already present in current source.

Codex observes three actionable issue clusters for the next build loop:

1. Public/local path boundary may still need defense-in-depth, especially `EligibilityCandidate.source_path` / `source_project_path` and frontend static source rows.
2. `monitoring_intake.py` is only a SAR-style/demo placeholder and must not be used for RUX real-data monitoring.
3. RUX P0 should start from original RUX listing + protocol, protocol-derived rules, field mapping, subject timeline, Patient Profile, review actions, audit trace, and independent AI runtime routing.

## Boundary Compliance

- Participant prompts were preflighted with `hermes_workflow_guard.py`.
- Initial prompt preflight failed because the generated prompts contained the absolute workspace path; Codex patched prompts to say "current workspace root" and reran preflight. All five prompts then passed.
- Participants were instructed to read only listed workspace files, not production/original real-project folders, not web, not tests, not browser/visual surfaces, and not source-edit.
- Participant output files:
  - `runs/conference/prior_work_rux_preflight_review_20260708/participant_qwen_plus.md` (366 lines)
  - `runs/conference/prior_work_rux_preflight_review_20260708/participant_mimo.md` (200 lines)
  - `runs/conference/prior_work_rux_preflight_review_20260708/participant_ds_flash.md` (320 lines)
  - `runs/conference/prior_work_rux_preflight_review_20260708/hermes_lead.md` (297 lines)
- Codex has not accepted any product-code edit from this conference before DeepSeek Pro review.

## Participant Outputs Reviewed

- qwen+:
  - Finds prior closure conditionally valid.
  - Flags static local paths in `frontend/src/App.jsx` as a medium path-leak/product-boundary risk.
  - Treats `monitoring_intake.py` as placeholder only and recommends a new RUX-specific component.
  - Recommends full regression before the next build loop.
- mimo:
  - Finds prior closure conditionally valid.
  - Escalates possible `source_project_path` leakage through the eligibility API and recommends `exclude=True` plus a test assertion.
  - Confirms current monitoring rules are demo/SAR-style and not RUX-ready.
  - Notes it did not read all 4,878 lines of `App.jsx`, so its absence-of-path statement is incomplete.
- ds_flash:
  - Finds prior closure conditionally valid.
  - Treats hardcoded local paths mostly as deployment/config risks rather than current user-facing leaks.
  - Recommends protocol-parameterized RUX monitoring and highlights AI-provider configuration as a prerequisite.
  - Provides a 10-gate RUX verification checklist.

## Hermes Sub-Venue Review

Completed in `runs/conference/prior_work_rux_preflight_review_20260708/hermes_lead.md`.

Chair synthesis:

- No participant rerun needed.
- Three-way consensus:
  - prior closure is conditionally valid;
  - `monitoring_intake.py` must remain placeholder only;
  - RUX monitoring must be rebuilt from original listing + protocol;
  - `_select_visible_items()` should not be removed until a better overview information architecture exists.
- Unresolved conflicts for Codex/DeepSeek Pro:
  - whether static `App.jsx` local paths should be fixed immediately;
  - whether `EligibilityCandidate.source_path` / `source_project_path` is a current public API leak or just defense-in-depth;
  - exact scope of "land now".
- Chair recommendation:
  - likely land now: one defense-in-depth path exclusion/test if confirmed by Codex;
  - mandatory before RUX P0: full backend regression, frontend build, overview QC, RUX parser verification, and AI provider route check;
  - defer RUX protocol rules, field mapper, risk engine, subject timeline, Patient Profile, audit trace, and provider routing into RUX P0.

## Main-Venue DeepSeek Pro Review

Completed in `runs/conference/prior_work_rux_preflight_review_20260708/main_deepseek_pro.md`.

DeepSeek Pro conclusions accepted by Codex:

- The Hermes advisory package is high quality and does not need participant reruns.
- Prior closure remains conditionally valid; before RUX P0, establish a fresh full-regression/frontend-build/browser-QC baseline.
- `monitoring_intake.py` is placeholder only; the intake pattern can remain, but the RUX rule engine must be protocol-parameterized.
- RUX P0 requires original listing + protocol only, plus a new D0 data dictionary/codebook before field mapping and rule evaluation.
- AI provider configuration and concurrency behavior must be verified before any runtime AI-dependent RUX monitoring task.

DeepSeek Pro recommendation corrected by Codex:

- Pro recommended a one-line exclusion for `EligibilityCandidate.source_path` / `source_project_path`, but Codex re-read the current contracts and router after Pro returned:
  - `EligibilityCandidate.source_path` already has `Field(default="", exclude=True)`.
  - `EligibilityTaskEntry.source_project_path` already has `Field(default="", exclude=True)`.
  - `EligibilityReviewDataset.source_path` already has `Field(default="", exclude=True)`.
  - `services/api/app/eligibility.py` returns `dataset.model_dump(mode="json")`, so Pydantic exclusions apply.
  - `tests/test_eligibility_adapter.py` already asserts the eligibility response does not contain `/Users/`, `source_path`, or `source_project_path`.
  - Focused tests passed after this re-check.

Therefore no eligibility path-leak code edit is needed in this round.

## Codex Independent Verification

Completed before DeepSeek Pro dispatch:

- Created `context/rux_monitoring_source_precheck_20260708.md` by parsing original RUX files through existing parsers:
  - RUX listing: 53 sheets, 180,793 rows.
  - RUX subject report: 192 rows.
  - RUX protocol: 2,005 paragraphs, 20 tables, 2,005 spans.
- `rg`/source scan confirmed `frontend/src/App.jsx` contains local absolute path strings in source-row definitions around the source registry/data sections; this is a real issue for Codex to adjudicate, even if not visible in default overview QC.
- `monitoring_intake.py` read directly: the rule engine currently has four generic/demo rules and SAR-like examples; it is not RUX-specific.
- No product-code edits have been made from the current Hermes review.
- Tests/browser QC were not run in this interim stage because no product code has been changed and DeepSeek Pro review is pending.

Completed after DeepSeek Pro returned:

- Read `services/api/app/eligibility.py`, `packages/contracts/workbench_contracts/models.py`, `services/api/app/enrollment_adapter.py`, and relevant tests to resolve the `source_project_path` disagreement.
- Confirmed `frontend/src/App.jsx` still contains local absolute paths in `sourceRegistryCandidates` and renders only `shortPath(candidate.path)` in the candidate card. This is not visible as `/Users/` in normal UI text, but it is still present in the frontend bundle and should be removed/refactored before productized distribution.
- Read `_select_visible_items()` directly. The guard is part of a short-term cross-module visibility patch. No edit made; it remains a commercialization backlog item.
- Ran focused verification:
  - `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_eligibility_adapter tests.test_contracts tests.test_listing_file_parser tests.test_protocol_text_extractor -v`
  - Result: 35 tests OK.
  - This included real RUX listing parse, real RUX subject report parse, and real RUX protocol DOCX parse tests on the current machine.

## Final Decision

Accepted for this advisory review. Product-code landing decision:

- No product-code edits landed from the current Hermes review.
- `App.jsx` static local paths remain a known latent productization issue and should be addressed in the next frontend/source-registry refactor or before distributing a production bundle.
- `monitoring_intake.py` remains a demo placeholder; RUX medical monitoring must not reuse its hardcoded SAR-style rules.
- Next build-loop entry gates:
  - fresh full backend regression, frontend build, and overview/browser QC;
  - RUX data dictionary/codebook;
  - protocol-derived rule schema covering protocol table 1, 4, and 7 concerns;
  - original RUX listing/protocol parse baseline;
  - independent AI provider connectivity/concurrency check.
