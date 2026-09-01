# Task Context: monitoring_record_rule_mapping_p7b

Created: 2026-07-29 21:33:17
Objective: Resolve P7B record anchors from the frozen confirmed field-mapping revision, exclude non-event timestamps, freeze mapping identity, preserve audited compatibility fallback, and test without touching frontend, writing, shared AI, or restarting API
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `context/monitoring_record_rule_resolution_p7b_context.md`
- `records/active_slices/medical_monitoring_goal_p7_20260729/P7B_HANDOFF_20260729.md`
- Frozen batch mapping persistence in `monitoring_batch_repository.py`
- Confirmed mapping revision and batch-binding lifecycle in
  `monitoring_mapping_draft_repository.py`,
  `monitoring_mapping_activation.py`, and
  `monitoring_mapping_batch_lifecycle.py`
- Existing P7A applicability resolver and P7B record-rule resolver tests

## Scope

- In scope: frozen batch mapping read contract; mapping-first centre, subject,
  and event-date anchors; closed role aliases; audited compatibility fallback;
  mapping identity in record-rule snapshots; P7B backend tests and handoff.
- Out of scope: frontend, medical writing, shared AI, API process restart,
  destructive migration, mapping authoring behavior, and new public endpoints.

## Success Criteria

- The exact confirmed mapping revision embedded in the frozen batch is read
  and integrity checked before first record-applicability resolution.
- Custom and Chinese source fields resolve through confirmed roles.
- PAGELMDT, source modification dates, and birth dates cannot become event
  dates; arbitrary date suffix guessing is absent.
- Missing, conflicting, excluded, or non-ISO anchors fail closed.
- Mapping revision and both content identities are frozen into the resolution
  hash and crash-recoverable rule snapshot.
- Existing applicability, unique published pack binding, multi-pack behavior,
  and project-effective compatibility remain green.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-29 21:33:17: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-29 21:39:30: Pre-change copies and SHA-256 manifest saved under
  `records/active_slices/medical_monitoring_goal_p7_20260729/p7b_mapping_prechange/`.
- 2026-07-29 21:40-21:49: Implemented frozen mapping contract, mapping-first
  anchor extraction, explicit excluded fields, audited fallback, and snapshot
  identity validation.
- 2026-07-29 21:49-21:52: Added repository and resolver tests for custom,
  Chinese, RUX, missing/conflicting/excluded mapping, fallback, identity
  tampering, and crash recovery.
- 2026-07-29 21:52-22:01: Focused tests passed (75); mapping/lifecycle adjacent
  set passed (125); broader P7 adjacent set passed (320).
- 2026-07-29 22:09: All `tests/test_monitoring_*.py` completed with
  `601 passed, 18 warnings`; warnings are existing FastAPI deprecations and
  source workbook parser warnings.
