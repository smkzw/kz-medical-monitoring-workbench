# Task Context: mw_ctgov_document_admission_20260729

Created: 2026-07-29 03:18:48
Objective: Align ClinicalTrials.gov Protocol/SAP content admission with official document metadata while preserving manual-upload publication/type checks, and prove the result against frozen r11 data without mutation.
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `context/mw_ctgov_document_type_authority_20260729.md`
- `context/mw_r11_document_preparation_failures_20260729.md`
- frozen r11 `writing_reference.sqlite3`
- `services/api/app/writing_reference.py`
- `tests/test_writing_reference_document_validation.py`
- ClinicalTrials.gov Results Data Element Definitions, Study Data Structure,
  Results QC Review Criteria, and official public document examples linked in
  the authority decision.

## Scope

- In scope: public registry document identity, study/NCT/indication binding,
  manual/non-registry content classification, focused tests, and read-only r11
  recomputation.
- Out of scope: mutating r11, automatic override, translation, OCR, AI role
  configuration, and ambiguous manual-document AI classification.

## Success Criteria

- Registry-bound Protocol/SAP/Protocol+SAP is not downgraded because an SAP
  repeats protocol language or a Protocol contains citations/references.
- Manual/non-registry publication substitution and Protocol/SAP boundaries
  remain strict and user-overridable.
- Relevant tests pass.
- Read-only recomputation changes all 45 r11 type mismatches to confirmed
  without override and introduces no new review/mismatch record.

## Risk Boundaries

- Product writes are limited to `services/api/app/writing_reference.py` and
  `tests/test_writing_reference_document_validation.py`; decision/task records
  are written under `context/`, `reviews/`, and `metrics/`.
- Frozen r11 evidence/database is read-only and may not be counted as a new
  E2E pass.
- Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-29 03:18:48: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-29: Official ClinicalTrials.gov document metadata authority and QC
  contract verified; heuristic-only expansion rejected.
- 2026-07-29: Focused and adjacent suite passed 47 tests.
- 2026-07-29: Read-only r11 recomputation evaluated 96 extracted documents:
  old 44 confirmed / 45 mismatch / 7 needs-review; new 96 confirmed, zero
  mismatch/needs-review, zero evaluation error.
