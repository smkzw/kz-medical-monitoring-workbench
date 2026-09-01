# Task Context: medical_monitoring_mapping_revision_presence_guard_20260804

Created: 2026-08-04 15:33:00
Objective: Make monitoring batch diff fail closed when mapping revision presence changes between snapshots; add focused regression and durable evidence without runtime, database, provider, browser, or real-project execution.
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_batch_diff.py`, especially `diff_monitoring_rows` and its
  `requires_rereview_keys` contract.
- `tests/test_monitoring_batch_diff.py` existing mapping-change and removal-resolution tests.
- `services/api/app/monitoring_batch_service.py` caller, which passes persisted mapping revisions
  as empty strings when a batch has no confirmed mapping.
- Current PRD/LOOP gate evidence: missing or changed mapping must not silently inherit a prior
  risk interpretation; this patch remains offline and does not authorize a batch.

## Scope

- In scope: make mapping-revision presence changes trigger `requires_rereview_keys`; add focused
  regression cases for old-present/new-missing and old-missing/new-present.
- In scope: update task evidence, review, metrics and LOOP ledger.
- Out of scope: changing row identity, removal eligibility, persisted batches, API routes, runtime,
  provider, browser/Playwright, real project files, medical judgments, or B6/C14 authority.

## Success Criteria

- Existing same-revision and changed-revision behavior remains passing.
- Either side missing while the other is present marks all matched rows for re-review.
- The result remains deterministic and no removal/resolution status is made more permissive.
- Focused diff tests, adjacent batch-service tests, Python compile and Hermes review-gate pass.
- Reserved ports 8911/5174/8910/4173 remain stopped and medical-writing files are untouched.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 15:33:00: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04 15:34:00: Audited the current diff predicate and caller; confirmed the unsafe case is
  asymmetric mapping-version presence, not a row-identity or removal algorithm defect. Selected a
  one-expression fail-closed change plus two regression cases.
- 2026-08-04 15:41:00: Implemented and verified the asymmetric presence guard. New regression,
  non-real diff, batch service, direct consumer suites and compile passed; Hermes review-gate is
  `ok=true`. Added LOOP 5.113 and kept all runtime/medical authority boundaries unchanged.
