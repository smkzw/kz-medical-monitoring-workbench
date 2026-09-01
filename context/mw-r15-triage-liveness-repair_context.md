# Task Context: mw-r15-triage-liveness-repair

Created: 2026-07-29 05:09:48
Objective: Implement and verify progress-aware parent waiting for live competitor-triage children, prevent retry/projection contradictions, then prepare a clean r15 A1 retest
Task type: `finite_code_task`
Risk: `high`
Selected agent route: `codebuddy-cli` / `hy3` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `context/mw-r14-triage-parent-timeout_conference_context.md`
- `runs/conference/mw-r14-triage-parent-timeout/general_aishuo_cms.md`
- `runs/conference/mw-r14-triage-parent-timeout/general_codebuddy_deepseek_pro.md`
- `runs/conference/mw-r14-triage-parent-timeout/general_chair_pi_qwen38.md`
- `runs/execution/mw_final_5x3_harness_20260728/rounds/release-r14-20260729/slots/A1/lazy_medical_writer/DEFECTS.md`
- `runs/execution/mw_final_5x3_harness_20260728/rounds/release-r14-20260729/slots/A1/lazy_medical_writer/BROWSER_ACTION_TRACE.json`
- `services/api/app/medical_writing_research_pipeline.py`
- `services/api/app/medical_writing_durable_jobs.py`
- `services/api/app/medical_writing_competitor_triage.py`
- `tests/test_mw_triage_deadline_reconcile_r10.py`
- `tests/test_medical_writing_research_pipeline_progress.py`
- `tests/test_medical_writing_durable_jobs.py`

## Scope

- In scope: implement the conference-selected progress/liveness-aware wait for
  competitor triage, using 1200 seconds without monotonic business-progress
  advance as the stall threshold and 7200 seconds as the absolute hard ceiling.
- In scope: preserve the completed-at-deadline r10 behavior; distinguish lease
  liveness from business progress; prevent timeout from causing a duplicate
  parent retry while the original child remains live; keep parent/child
  progress and terminal projection consistent; clear stale error summaries
  when a retry-wait job is reclaimed.
- In scope: add focused deterministic regression tests and run the directly
  affected test suites.
- Writable product paths are limited to:
  `services/api/app/medical_writing_research_pipeline.py`,
  `services/api/app/medical_writing_durable_jobs.py`, and directly related test
  files under `tests/`.
- Out of scope: event-driven pipeline redesign, frontend redesign, P1 transient
  `competitor-triage/latest` 404, corpus-gate changes, clinical scenario
  changes, and creating a PASS artifact.

## Success Criteria

- A child that remains active and advances monotonic business progress beyond
  the original 900-second edge does not make the parent fail or retry.
- Lease heartbeat alone does not reset the 1200-second business-stall window.
- The parent stops after the 7200-second absolute ceiling even if intermittent
  progress continues.
- Completed/review-ready, failed/cancelled, cancellation, graceful shutdown,
  idempotency, and stale-owner behavior remain correct.
- No UI/API state can report terminal parent failure at 100% while a bound
  child is still live and progressing.
- Timeout handling does not start duplicate competitor AI work.
- Reclaimed retry-wait jobs do not retain stale `error_summary`.
- Focused tests pass and changed files compile.

## Risk Boundaries

- The r14 isolated runtime is stopped; this is a new bounded repair round.
- Do not touch shared runtime data or r14 evidence.
- Product writes are limited to the explicit writable files above.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-29 05:09:48: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-29: the default aishuo finite-code route is forbidden by the
  00:00-08:30 Beijing rule; the effective worker route is CodeBuddy CLI / hy3
  at maximum effort. Cursor CLI / auto is the execution manager.
- 2026-07-29: both delegated execution sessions returned useful design reviews
  but were read-only and made no product-source changes. Codex applied the
  bounded repair directly inside the declared write scope.
- 2026-07-29: implemented monotonic business-progress waiting, a 1200-second
  stall threshold, 7200-second absolute ceiling, typed non-retryable parent
  detachment, recoverable `triaging` journey projection, retry-wait stale-error
  clearing, and idempotent stage/progress reconciliation.
- 2026-07-29: independent Luna-high delta review completed. Codex accepted the
  monotonic-clock and real-worker coverage findings, rejected coupling domain
  recovery to the durable job-row completion CAS, and deferred the separate
  already-`confirmed` stale-parent semantic.
- 2026-07-29: 391 unique targeted regression tests passed, including the real
  `DurableJobWorker`, inline fallback, frontend contracts and final 5x3
  harness/runtime suites. Review record:
  `reviews/codex_mw-r15-triage-liveness-repair_review.md`.

## Changed Artifacts

- `services/api/app/medical_writing_research_pipeline.py`
- `services/api/app/medical_writing_durable_jobs.py`
- `tests/test_mw_triage_deadline_reconcile_r10.py`
- `tests/test_medical_writing_durable_jobs.py`
- `tests/test_mw_r5_a1_batch_repair.py`

## Next Safe Action

Freeze the changed-source hashes, prepare `release-r15-20260729`, start a new
zero-project A1 lazy-medical-writer runtime, verify all four product AI roles,
then run the full visible COPD Phase III inhaled-combination journey with the
corrected long-wait contract.
