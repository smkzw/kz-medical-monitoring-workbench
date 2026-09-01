# Task Context: mw_triage_deadline_reconcile_r10

Created: 2026-07-28 23:33:00
Objective: Repair parent research-pipeline timeout when the durable competitor-triage child reaches review_ready at the deadline, without duplicate triage or gate weakening
Task type: `finite_code_task`
Risk: `high`
Selected agent route from initializer: `aishuo` / `cms-model` / `high`
Effective night route: `pi` / `alibaba` / `qwen3.8-max-preview` / `xhigh`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Frozen release-r10 evidence:
  - `runs/execution/mw_final_5x3_harness_20260728/rounds/release-r10-20260728/slots/A1/lazy_medical_writer/DEFECTS.md`
  - `runs/execution/mw_final_5x3_harness_20260728/rounds/release-r10-20260728/slots/A1/lazy_medical_writer/pipeline_lineage.json`
  - `runs/execution/mw_final_5x3_harness_20260728/rounds/release-r10-20260728/slots/A1/lazy_medical_writer/durable_jobs_readonly_snapshot.txt`
  - `runs/execution/mw_final_5x3_harness_20260728/rounds/release-r10-20260728/slots/A1/lazy_medical_writer/readonly_database_snapshot.json`
- `services/api/app/medical_writing_research_pipeline.py`
- Directly affected research-pipeline and durable-job tests.

## Scope

- In scope:
  - reproduce the 900-second deadline boundary where the child durable job
    reaches `completed/review_ready` immediately before the parent's polling
    loop exits;
  - make one final authoritative child-job and triage-run reconciliation before
    declaring timeout;
  - persist `awaiting_triage_confirm` with current 19/19 progress when the same
    run and snapshot are review-ready;
  - ensure retries reuse the same child run and never duplicate AI triage;
  - add deterministic tests for deadline-edge completion and genuine timeout.
- Out of scope:
  - changing timeout duration merely to hide the race;
  - modifying frozen r10 evidence/databases;
  - changing search, basket-confirmation, preparation, translation, corpus or
    clinical gates;
  - broad progress-UI redesign or the transient pre-run latest 404.

## Success Criteria

- A child that is completed/review-ready at the deadline cannot be reported as
  parent `分诊超时`.
- A genuinely incomplete child still fails truthfully after the deadline.
- Parent state/progress agrees with the durable child and no retry control is
  offered for an already review-ready run.
- Existing pipeline/recovery/idempotency tests remain green.

## Risk Boundaries

- Edit only the workbench implementation and directly affected tests.
- Frozen r10 artifacts remain read-only.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-28 23:33:00: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-28 23:34: Initial Aishuo route was outside the user-authorized
  start window. Effective route substituted to Pi/alibaba/qwen3.8-max-preview
  xhigh before dispatch.
- 2026-07-29 00:08: Worker repair and Cursor manager review were reconciled.
  The manager correctly identified that deadline-edge success must return the
  same value as in-window completion; otherwise `auto_confirm_triage=True`
  would return early.
- 2026-07-29 00:08: Codex applied the required follow-up and added a direct
  `execute_stages(auto_confirm_triage=True)` regression proving that
  `continue_after_triage` is invoked exactly once at the deadline edge.
- 2026-07-29 00:08: Dedicated tests passed 9/9; directly affected suites passed
  86/86; Python compilation passed. Accepted for a clean release-r11 only.

## Accepted Hashes

- `services/api/app/medical_writing_research_pipeline.py`:
  `5276cb545e5288a1efdfd71b5bb16f403ec8f910d0919c99122aa95b54d4f628`
- `tests/test_mw_triage_deadline_reconcile_r10.py`:
  `dd007523a1d4881274ccc8e2c55dbde2784a74f6c22a2b93b247d24a16d9bf2a`

## Next Safe Action

Create `release-r11-20260729` with refreshed source receipts and start a fresh
A1 lazy medical-writer runtime. Do not reuse the r10 project, databases, ports,
browser profile, or evidence directory.
