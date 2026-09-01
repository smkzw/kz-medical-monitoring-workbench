# Task Context: medical_monitoring_assurance_task_root_read_shape_revalidation_20260805

Created: 2026-08-05 04:59:00
Objective: Fail closed on malformed persisted monitoring assurance task root fields
Task type: `finite_code_task`
Risk: `high`
Selected agent route: `alibaba` / `qwen3.8-max` / `xhigh`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_assurance_repository.py` (`AssuranceTask`,
  `_task_from_row`, task schema and lifecycle readers/writers).
- `tests/test_monitoring_assurance.py`,
  `tests/test_monitoring_assurance_principal_route.py`, and the existing
  assurance/proof/rollup/release-dossier suites.
- Current filesystem state and
  `records/active_slices/medical_monitoring_goal_p10_20260730/LOOP_LEDGER.md`.
- Real-loop/release gates remain authoritative and blocked; this slice is
  source-only and cannot activate runtime or external providers.

## Scope

- In scope: fail closed on malformed assurance task mode/status/version and
  required timestamps, preserve valid task lifecycle/identity behavior, add
  focused tamper regressions, run assurance adjacency, compile/Ruff, hashes,
  evidence and review gate.
- Out of scope: services, ports, browsers/Playwright, real project data,
  external providers, medical judgments, new task identity/schema schemes, and
  runtime/release activation.

## Success Criteria

- Valid assurance task roots round-trip unchanged across restart and lifecycle
  reads.
- Invalid/missing timestamps, unknown mode/status or non-integral version fail
  closed without substituting the current time.
- Focused/adjacent tests, compileall, Ruff and reserved-port checks pass; the
  evidence records exact counts, hashes, warnings and residual limits.
- Review gate reports `ok: true` with no warnings/errors.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- No provider/sub-agent dispatch is permitted in this turn; Codex performs the
  bounded change and final verification directly.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 04:59:00: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05: Codex direct execution selected; no external provider or
  sub-agent dispatch.
- 2026-08-05 07:21: Extended `_task_from_row` to reject padded/non-string
  persisted creator and optional task text; focused assurance/principal 97
  passed, compileall passed, reserved ports stayed empty, and current Ruff
  availability was recorded as unverified.
- 2026-08-05: Implemented and verified strict assurance task-root mode/status/
  version/timestamp reads; focused 77 and adjacent 197 passed,
  compileall/Ruff passed, reserved ports remained free, and the Hermes review
  gate returned `ok: true`.
- 2026-08-05: Next action is another bounded source-only P7/P8/P9 integrity
  gap; provider/runtime/real-loop gates remain closed.
