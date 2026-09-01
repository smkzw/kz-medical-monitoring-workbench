# Task Context: medical_monitoring_daily_run_root_input_hash_revalidation_20260805

Created: 2026-08-05 04:29:49
Objective: Harden persisted daily-run root reads by recomputing the existing DailyRunInput input hash while preserving runtime lifecycle fields
Task type: `finite_code_task`
Risk: `high`
Selected agent route: `alibaba` / `qwen3.8-max` / `xhigh`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_daily_run_repository.py` (`DailyRunInput`,
  `MonitoringDailyRun`, `_run` and create/get/list paths)
- `tests/test_monitoring_daily_run_repository.py` plus existing daily-run,
  AI, assurance, mapping, rule, and API consumers.
- Current filesystem state and `records/active_slices/medical_monitoring_goal_p10_20260730/LOOP_LEDGER.md`.
- Real-loop/release gates remain authoritative and blocked; this slice is
  source-only and cannot activate runtime or external providers.

## Scope

- In scope: recompute the existing `DailyRunInput.input_sha256` on persisted
  root-run reads and fail closed on input drift, while preserving lease,
  snapshot, status, CAS and confirmation fields.
- In scope: add focused tamper regressions, run focused and adjacent daily-run/
  mapping/AI/rule/assurance/API tests, compile/Ruff checks, hashes, evidence,
  and review gate.
- Out of scope: services, ports, browsers/Playwright, real project data,
  external providers, medical judgments, release activation, or changes
  outside the workbench.

## Success Criteria

- A persisted root run whose batch/mapping/rule/engine input fields drift from
  its stored `input_sha256` fails closed on get/list/active reads.
- A valid run and all mutable lifecycle fields round-trip unchanged; existing
  snapshot, lease, CAS, migration and confirmation tests remain green.
- Focused and adjacent tests, compileall, Ruff, and reserved-port checks pass;
  evidence records exact commands, counts, hashes, warnings, and residual
  limits.
- Review gate reports `ok: true` with no warnings/errors.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- Do not hash mutable lease/status/snapshot fields into the input identity; only
  the existing `DailyRunInput` normalized fields are immutable run inputs.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 04:29:49: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05 04:30:00: Codex direct execution selected; no external provider or sub-agent dispatch is permitted in this turn.
- 2026-08-05: `_run()` now reconstructs `DailyRunInput`, rechecks `input_sha256`, and preserves lifecycle fields; focused suite reached 21 passed.
- 2026-08-05: Daily-run/AI/analysis/router/record-rule/P0 adjacent group reached 165 passed; compileall and Ruff passed; reserved ports remained free.
- 2026-08-05: Review evidence is ready for Codex direct completion; no runtime/provider/browser/real-project action occurred and real-loop/release gates remain blocked.
- 2026-08-05 04:30:00: Codex direct execution selected; no external provider or sub-agent dispatch is permitted in this turn.
