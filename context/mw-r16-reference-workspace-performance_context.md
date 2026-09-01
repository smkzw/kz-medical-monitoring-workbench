# Task Context: mw-r16-reference-workspace-performance

Created: 2026-07-29 08:14:37
Objective: Repair and regress the real r15 references/workspace timeout, preserve frozen evidence, and prepare a clean A1 rerun
Task type: `finite_code_task`
Risk: `high`
Selected agent route: Codex direct repair plus `gpt-5.6-luna` high read-only delta review

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `runs/execution/mw_final_5x3_harness_20260728/rounds/release-r15-20260729/slots/A1/lazy_medical_writer/BLOCKED.md`
- `runs/execution/mw_final_5x3_harness_20260728/rounds/release-r15-20260729/slots/A1/lazy_medical_writer/DEFECTS.md`
- `runs/execution/mw_final_5x3_harness_20260728/rounds/release-r15-20260729/slots/A1/lazy_medical_writer/runtime/writing_reference.sqlite3`
- `services/api/app/main.py:get_writing_reference_workspace`
- `services/api/app/writing_reference_repository.py`
- `tests/test_writing_reference_repository.py`
- `tests/test_writing_reference_upper_layer_execution.py`
- `tests/test_writing_reference_api.py`

## Scope

- In scope: preserve the immutable r15 blocker evidence; identify the exact
  repository operation behind the `references/workspace` timeout; implement an
  additive migration that makes the current-snapshot workspace fast on the
  real 70-document/56,691-span database; verify old-database migration,
  latest-extraction semantics, API response completeness and frontend
  workspace contracts.
- In scope: add the changed repository and tests to the 5x3 authoritative
  source hash set after all concurrent shared-file writes have stabilized.
- Out of scope: bypassing content/structure admission, changing corpus gates,
  mutating the r15 runtime, declaring r15 passed, or accepting the next A1 run
  without a new clean project.

## Success Criteria

- Schema v6 databases migrate additively to v7 without losing rows or changing
  latest-extraction span-count semantics.
- The frozen r15 database returns the complete 665-candidate/70-document
  workspace through the real FastAPI endpoint in under two seconds.
- Repository, migration, API and frontend reference-workspace tests pass.
- A new clean A1 visible-browser run reaches document validation without the
  previous loading deadlock.

## Risk Boundaries

- The r15 evidence runtime is read-only. Performance experiments use copied
  databases under `/tmp`.
- Writable product paths are limited to
  `services/api/app/writing_reference_repository.py` and directly related
  tests/config/records.
- Concurrent medical-monitoring work owns `services/api/app/main.py` and
  `frontend/src/App.jsx`; do not revert or edit those files in this slice.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-29 08:14:37: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-29: r15 A1 completed ClinicalTrials.gov search (665 studies),
  competitor triage (19/19) and document preparation (70/70), then froze at
  `awaiting_document_validation`; the workspace request exceeded 120 seconds.
- 2026-07-29: method-level profiling on a copy of the frozen database isolated
  `source_span_counts()` as the sole slow component. It scanned 56,691 spans
  against the latest extraction per artifact without composite indexes.
- 2026-07-29: two candidate indexes reduced the raw query to about 0.01 seconds
  and complete repository workspace assembly to about 0.03 seconds.
- 2026-07-29: implemented schema v7 with additive latest-extraction and
  artifact/revision span indexes. Focused repository/API/frontend tests passed
  145/145.
- 2026-07-29: a fresh copy of the frozen v6 database migrated to v7 in 0.47
  seconds. The complete 1.68 MB workspace returned through the real FastAPI
  endpoint with HTTP 200 in 0.082 seconds.
- 2026-07-29: next-round harness validation correctly stopped because
  concurrent medical-monitoring work changed shared `main.py` and `App.jsx`.
  Those changes are preserved; hashes will be refreshed only after that writer
  finishes.
- 2026-07-29: independent read-only review
  `019fab3a-2cb5-7553-9d53-97778c3a6406` identified three material risks:
  concurrent schema initialization, cross-snapshot span counts, and
  non-deterministic latest-extraction ties. The review also noted the expected
  index size increase.
- 2026-07-29: remediation added a cross-process repository initialization
  lock, transactional/idempotent v7 migration, a snapshot-aware document
  index and deterministic `created_at + extraction_revision` ordering.
  `references/workspace` now passes its exact bound snapshot into
  `source_span_counts`.
- 2026-07-29: 20 independent-process initialization rounds passed
  (10 fresh and 10 v6 databases, 8 concurrent processes per round). Focused
  reference/API/frontend regression passed 148 tests; the broad medical
  writing chain passed 1,032 tests.
- 2026-07-29: shared medical-monitoring protection passed 227 Python tests and
  all four Node contract suites (`37`, `40`, `27`, and subject-model suite).
- 2026-07-29: final read-only copy of the frozen r15 v6 database migrated to v7
  in 0.2734 seconds. The real FastAPI route returned HTTP 200 in 0.0791 seconds
  with 1,680,912 bytes, all 665 candidates, all 70 artifacts, and span counts
  for all 70 artifacts. The frozen source database remained unchanged.
