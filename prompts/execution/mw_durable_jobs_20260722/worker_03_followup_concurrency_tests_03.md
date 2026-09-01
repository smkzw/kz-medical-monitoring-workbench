Continue the same `mw_durable_jobs_20260722 / worker_03` session. Your previous `WORKER_03_REVISION_INTEGRATION_V2_COMPLETE` marker is rejected because the implementation and tests do not satisfy the explicit contract. Reread `/Users/smkzw/.hermes/SOUL.md`, workspace `AGENTS.md`, the previous prompt/report, and current source before editing.

## Hard boundaries

- Work only inside the runner-provided current workspace (`.`).
- Write only `services/api/app/medical_writing.py`, `services/api/app/medical_writing_repository.py`, `tests/test_medical_writing_revision_durable.py`, `tests/test_medical_writing_revision_application.py`, plus a minimal targeted `services/api/app/sqlite_runtime_store.py` change only if a table atomicity defect requires it.
- Do not edit `main.py`, frontend, shared durable core, triage, translation, exporter, contracts, or unrelated tests.
- Runner-managed output file: `runs/execution/mw_durable_jobs_20260722/worker_03_followup_concurrency_tests_03.md`. Never write it with tools; return the report in final text.

Read initially:
- `AGENTS.md`
- `runs/execution/mw_durable_jobs_20260722/worker_03_followup_integration_02.md`
- `services/api/app/medical_writing.py`
- `services/api/app/medical_writing_repository.py`
- `services/api/app/sqlite_runtime_store.py`
- `tests/test_medical_writing_revision_durable.py`
- `tests/test_medical_writing_revision_application.py`

Codex findings from current source:

## P0-A: shared-service repo monkey-patching is concurrency-unsafe

`prepare_revision_submission` and `prepare_rewrite_action` temporarily assign `self.repo = _CapturingRepo(...)`. The production resolver intentionally returns shared service instances. Two concurrent durable jobs using that service can capture each other's commits, read through the wrong proxy, restore `self.repo` out of order, lose a thread/audit, or accidentally persist before ownership proof. This creates new cross-project/cross-job corruption risk.

Required fix:
1. Remove `_CapturingRepo` and every temporary mutation of `self.repo`.
2. Refactor the original synchronous methods around pure preparation helpers: build validated `RevisionThread`/`AuditEvent` (and rewrite previous/updated thread/action result) without persistence; synchronous `submit_revision`/`apply_action` then call the same helper followed by their existing commit. The durable executor calls the helper, proves ownership, then calls the same commit. Preserve one canonical AI/prompt/evidence path; no duplicate reduced-quality algorithm.
3. Ensure preparation mutates only a deep working copy, never an object retained by an in-memory repository before commit.
4. Add a deterministic concurrency test with a barrier and two simultaneous initial/rewrite preparations on one shared service. Prove no repository swapping occurs, each project/job receives only its own thread/audit, and losing ownership for one cannot suppress or capture the other's commit.

## P0-B: required old-owner tests were not implemented

The previous report only added `cancel_before_start`; that does not test the defect. Add deterministic tests for both initial submission and rewrite where product AI completes and then, before business commit:
- `cancel_check` flips true;
- `cancel_check` raises;
- heartbeat returns false;
- heartbeat raises;
- simulated lease/takeover makes ownership false.

For every case assert no new initial revision thread/audit and no rewrite turn/status/audit mutation. Then rerun with a valid owner and prove exactly one commit. Include a late old-owner result after a new owner succeeds and prove it cannot overwrite/cross-capture.

## P0-C: table-cell atomic adoption remains unproven

The previous prompt explicitly required table-cell success, stale revision, anchor drift/wrong cell, rich-text preservation, idempotent replay, and injected failure tests. The report admits none were added, yet emitted completion. Build a real table working-copy fixture by reusing/adapting the existing table-cell tests in `tests/test_medical_writing_revision_application.py` and table editor fixtures. Add all required cases. Verify after each injected failure that thread/suggestions, working copy, audit/snapshots/idempotency remain pre-action and clean retry commits once. Do not claim transformation equivalence as test evidence.

## P1-D: service routing test is not an execution test

The current test only invokes private `_resolve()` twice. Replace/extend it so two real executor `execute()` calls use distinct project services and durable payloads, exercise prepare+commit, and prove no cross-project business writes. Include concurrent execution on the shared resolver.

## Completion gate

Run the four required suites from the previous prompt plus new deterministic tests. Inspect current diff for duplicate logic and shared mutable service state. Return exact counts and source locations.

Only emit `WORKER_03_REVISION_CONCURRENCY_V3_COMPLETE` when P0-A/B/C and P1-D are directly covered and pass. Otherwise return the remaining blocker without any completion marker.
