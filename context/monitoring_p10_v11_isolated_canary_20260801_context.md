# Task Context: monitoring_p10_v11_isolated_canary_20260801

Created: 2026-08-01 19:16:36
Objective: Execute exactly one isolated v11 visit-window canary on the frozen fresh clone, wait once to terminal, freeze evidence, and stop without retry or candidate action
Task type: `code_open_audit`
Risk: `critical`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Current filesystem and latest global/workbench `AGENTS.md`.
- Fresh isolated runtime:
  `runs/execution/monitoring_p10_v11_zero_submit_gate_20260801/runtime_zero_submit/`
- `runs/execution/monitoring_p10_v11_zero_submit_gate_20260801/ZERO_SUBMIT_EVIDENCE.md`
- Luna zero-submit review: PASS/P0-P4 none and authority for exactly one POST
  with the exact route/body below.
- Accepted six v11 hashes recorded in the zero-submit task context.

## Scope

- In scope:
  - recheck six hashes, authoritative comparison hashes, 8911/5174 stop state,
    v11 jobs=0 and active jobs=0;
  - start one 8911 backend on the exact fresh clone with parallelism one;
  - issue exactly one POST:
    `/api/projects/proj_rux_03_002/modules/medical-monitoring/protocol-preparation/protocol-versions/protov_21c4b5a4a3883a8119d74e18/start`
    with `{"topic_ids":["visit_window_and_order"]}`;
  - run one internal long-wait observer to terminal or the authorized hard
    wait; freeze the actual v11 input and terminal lineage;
  - stop 8911 immediately at terminal evidence.
- Out of scope:
  - any second POST, retry, reuse, salvage, reclassification or candidate
    decision;
  - second topic/project, 5174/browser, authoritative runtime or 18911;
  - clinical/release acceptance.

## Success Criteria

- Pre-POST hashes and zero-job/zero-active gates pass.
- Exactly one distinct v11 job is created by one HTTP 202 response.
- The single observer captures terminal status, attempt, request/response
  hashes, provider output count and candidate count without intervention.
- The v9/v10 frozen histories remain unchanged.
- 8911 is stopped; 5174 remains stopped; 18911 and authoritative hashes remain
  untouched.

## Risk Boundaries

- Writes are limited to the already isolated runtime and this task's
  context/review/metrics/evidence/LOOP records.
- Any pre-POST drift cancels the authorization and stops 8911.
- Terminal success, failure or hard-wait boundary never authorizes retry or
  candidate action.
- The historical GET revision/span count is not treated as a prediction of the
  fresh v11 input; record the actual start result.

## Timeout Policy

- One launch, one POST and one observer with up to the 120-minute hard wait.
- No controller polling, re-dispatch or intervention for latency.
- Stop at terminal or hard-wait return.

## Loop Log

- 2026-08-01 19:16:36: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- Luna independently reviewed the zero-submit evidence and authorized only the
  exact single RUX `visit_window_and_order` POST on the isolated clone.
- Pre-POST gates passed. PID 7712 started once on the exact clone with
  parallelism one. One POST returned 202 and created only
  `monai_3632c414655546ad250ce8bf7dbd`.
- The fresh start resolved source revision
  `mpr_40b82826a43e46342344841242e6` with 173 evidence spans; it did not reuse
  the historical GET snapshot.
- The one observer reached terminal
  `failed/invalid_ai_output/retryable=0`, one attempt, two provider outputs and
  zero candidates. The repair retained `药物回收相关段落` in a claim
  uncertainty, so the full boundary gate continued to reject excluded
  dispensing/return wording.
- 8911 was stopped immediately. No retry, reuse, salvage, reclassification or
  candidate action occurred. Frozen v9/v10 and authoritative hashes remained
  exact. Evidence:
  `runs/execution/monitoring_p10_v11_isolated_canary_20260801/TERMINAL_EVIDENCE.md`.
