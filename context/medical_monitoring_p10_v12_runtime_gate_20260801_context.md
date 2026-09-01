# Task Context: medical_monitoring_p10_v12_runtime_gate_20260801

Created: 2026-08-01 22:29:37
Closed: 2026-08-01 22:54 CST
State: **A6 zero-submit and one bounded RUX canary complete; runtime stopped**
Objective: Create a brand-new isolated v12 runtime clone, prove zero-submit invariants, and if the gate passes run at most one RUX visit_window_and_order canary without touching v9-v11 history or authority runtime.
Task type: `code_open_audit`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `context/monitoring_p10_v12_offline_corrective_pause_20260801.md`
- `context/monitoring_p10_v11_canary_pause_20260801.md`
- `runs/execution/monitoring_p10_v11_isolated_canary_20260801/TERMINAL_EVIDENCE.md`
- `runs/execution/monitoring_p10_v11_zero_submit_gate_20260801/ZERO_SUBMIT_EVIDENCE.md`
- final v12 governed source/test hashes recorded in the v12 pause checkpoint
- current workbench filesystem and the latest global/workbench `AGENTS.md`
- source runtime candidate only: the stopped v11 zero-submit clone under
  `runs/execution/monitoring_p10_v11_zero_submit_gate_20260801/runtime_zero_submit/`

No authoritative product runtime is a source for writes. The new v12 clone must
be produced under this task's run directory, and all runtime writes must remain
inside that run directory.

## Scope

- In scope: source/test hash and listener prechecks; a new SQLite-backup clone;
  manifest and integrity checks; health/readiness/status GETs; v12 zero-job and
  frozen-history comparisons; and, only if every zero-submit assertion passes,
  one RUX `visit_window_and_order` POST followed by a single terminal wait and
  immediate service stop.
- Out of scope: v9-v11 retry/reuse/salvage/reclassification; authoritative
  runtime or 18911 writes; 5174 startup; second topic/project; three-project
  loop; browser/UI execution; Phase B source changes; provider configuration
  changes; and any candidate adoption without Codex review.

## Success Criteria

- Six governed v12 hashes match the offline pause checkpoint before any runtime
  action.
- 8911 and 5174 are stopped and PID 43191 on 18911 is untouched.
- The source clone is copied using SQLite backup semantics, has no symlinks,
  preserves source-empty files, and has integrity `ok` for every non-empty
  SQLite main.
- Pre-GET and post-GET job/attempt/candidate comparisons show no v12 job, no
  active job and no unmarked v4-v11 job; frozen v9-v11 records remain unchanged.
- Only if the zero-submit gate passes: one POST for one RUX topic creates at
  most one v12 job; the worker reaches terminal state; there are zero illegal
  candidates; and 8911 is stopped immediately after observation.
- Evidence, review, metrics and LOOP records are persisted; no commercial
  release claim is made from this single canary.

## Risk Boundaries

- Never write the authoritative product runtime or any path outside the task run
  directory; do not touch 18911/PID 43191.
- Keep v9-v11 jobs immutable and do not migrate this clone into authority.
- Keep provider secrets/configuration read-only; do not print credentials.
- Use one listener only on 8911, parallelism 1, one long wait, no controller
  polling or redispatch; stop immediately on terminal observation.
- Codex is final authority. No external agent or conference is used for this
  direct task.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-01 22:29:37: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-01 22:31 CST: Re-read current AGENTS, v12 pause, v11 pause and terminal/
  zero-submit evidence. Decision: proceed to a brand-new isolated zero-submit
  clone; do not reuse the v11 clone as the target and do not start 5174.
- 2026-08-01 22:42 CST: Zero-submit GET gate passed on the new clone:
  21 mains, 18 integrity-ok, 3 source-empty, protocol v12 0/0/0, active 0,
  frozen v9-v11 rows/attempts/candidates unchanged.
- 2026-08-01 22:49 CST: Exactly one RUX topic POST returned 202. Job
  `monai_343e98b4992acc36e0c60da30e98` reached `completed` with one
  `success_repaired` attempt and three proposed candidates.
- 2026-08-01 22:50 CST: 8911 stopped immediately after terminal observation;
  5174 remained stopped and PID 43191/18911 was untouched.

## Terminal Evidence

- Zero-submit: `runs/execution/monitoring_p10_v12_zero_submit_gate_20260801/ZERO_SUBMIT_EVIDENCE.md`
- Canary terminal: `runs/execution/monitoring_p10_v12_zero_submit_gate_20260801/TERMINAL_EVIDENCE.md`
- Clone manifest: `runs/execution/monitoring_p10_v12_zero_submit_gate_20260801/CLONE_MANIFEST.json`
- Candidate evidence:
  `runs/execution/monitoring_p10_v12_zero_submit_gate_20260801/CANARY_CANDIDATE_EVIDENCE.json`
- Terminal runtime snapshot:
  `runs/execution/monitoring_p10_v12_zero_submit_gate_20260801/CANARY_TERMINAL_SNAPSHOT.json`

## Codex Closure Judgment

- The A6 runtime gate is accepted for this bounded single-topic canary.
- The v12 live run demonstrates successful one-repair recovery: initial output
  had three governed boundary hits (`回收`, `PK`, `安全性随访`) and the repaired
  output had zero; all three persisted candidates are `proposed` and source
  bound.
- This is not a commercial release decision. Browser/UI, three-project
  execution, full scientific acceptance, failure/restart matrix and Phase B
  shared-risk authority remain open.
