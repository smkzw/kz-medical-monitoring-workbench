You are Cursor CLI acting as the execution manager for the tracked task
`mw-r15-triage-liveness-repair`.

Work only inside the current workspace (`.`). Read and comply with `AGENTS.md`.
This is an authorized bounded code-edit round. Do not touch shared runtime
data, prior r13/r14 evidence, or unrelated files. Preserve unrelated changes.

Hard boundaries:

- Work only inside the current workspace (`.`).
- Do not touch shared runtime data or prior run evidence.
- Edit only the explicit writable scope below.
- Do not claim browser or release acceptance.
- Runner-managed output path:
  `runs/mw-r15-triage-liveness-repair-manager.md`. Never write this report
  path with tools; return the complete handoff and let the runner persist it.

Read these files only:

- `context/mw-r15-triage-liveness-repair_context.md`
- `runs/hermes_mw-r15-triage-liveness-repair.md`
- `runs/conference/mw-r14-triage-parent-timeout/general_aishuo_cms.md`
- `runs/conference/mw-r14-triage-parent-timeout/general_codebuddy_deepseek_pro.md`
- `runs/conference/mw-r14-triage-parent-timeout/general_chair_pi_qwen38.md`
- `services/api/app/medical_writing_research_pipeline.py`
- `services/api/app/medical_writing_durable_jobs.py`
- `tests/test_mw_triage_deadline_reconcile_r10.py`
- `tests/test_medical_writing_research_pipeline_progress.py`
- `tests/test_medical_writing_durable_jobs.py`

Writable scope:

- `services/api/app/medical_writing_research_pipeline.py`
- `services/api/app/medical_writing_durable_jobs.py`
- directly related tests under `tests/`

Implement the conference-selected repair:

1. Use a dedicated triage wait-timeout exception.
2. Replace the fixed 900-second parent failure with a liveness-aware wait:
   monotonic completed chunk/step advancement is business progress; lease
   heartbeat is only liveness and must not reset the business-progress timer.
   The no-business-progress threshold is 1200 seconds and the absolute hard
   ceiling is 7200 seconds.
3. Preserve cancellation, truthful child failure/cancellation, r10
   completed-at-edge reconciliation, monotonic progress, idempotency,
   graceful shutdown, and stale-owner isolation.
4. A live/progressing child must never make the parent present terminal
   failed/100% or automatically start duplicate competitor AI work.
5. Timeout handling must not retry the whole parent while the original child
   remains live. Use a precise exception type, not string matching.
6. Clear stale `error_summary` when a retry-wait durable job is reclaimed.
7. Add deterministic tests for:
   - progress continuing beyond the original 900-second edge;
   - lease heartbeat alone not counting as business progress;
   - a dead/no-lease 1200-second stall;
   - the 7200-second absolute ceiling despite intermittent progress;
   - no duplicate parent retry / consistent projection;
   - stale error cleanup on retry claim;
   - unchanged r10 completion/failure/cancellation contracts.

Review the worker's proposed patch critically; correct its semantics where
needed. In particular, do not keep waiting until 7200 merely because a live
lease heartbeats forever after 1200 seconds without business progress. The
1200-second business-stall threshold is itself a timeout; lease liveness helps
diagnose and present the state but does not waive the stall threshold.

Run focused pytest suites and Python compilation. Return a concise manager
handoff with changed files, behavior, exact test commands/results, unresolved
risks, and any decision requiring Codex. Do not create r15 harness or PASS
artifacts, and do not claim browser acceptance. The runner manages
`runs/mw-r15-triage-liveness-repair-manager.md`; do not write that file through
tools.
