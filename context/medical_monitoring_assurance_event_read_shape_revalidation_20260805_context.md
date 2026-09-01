# Task Context: medical_monitoring_assurance_event_read_shape_revalidation_20260805

Created: 2026-08-05 05:02:30
Objective: Fail closed on malformed or misbound persisted monitoring assurance lifecycle events
Task type: `finite_code_task`
Risk: `high`
Selected agent route: `alibaba` / `qwen3.8-max` / `xhigh`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_assurance_repository.py` (`AssuranceEvent`,
  `_row_to_event`, `list_events`, lifecycle event schema/writes).
- `tests/test_monitoring_assurance.py` plus assurance principal,
  proof/rollup, release-gate and dossier suites.
- Current filesystem state and
  `records/active_slices/medical_monitoring_goal_p10_20260730/LOOP_LEDGER.md`.
- Real-loop/release gates remain authoritative and blocked; this slice is
  source-only and cannot activate runtime or external providers.

## Scope

- In scope: validate ordinary lifecycle event task/project binding, integer
  sequence/version, object payload and ISO timestamp on reads; preserve the
  signed audit-chain path, ordering and event writes; add focused tamper
  regressions, run assurance adjacency, compile/Ruff, hashes, evidence and
  review gate.
- Out of scope: services, ports, browsers/Playwright, real project data,
  external providers, medical judgments, new event hash/schema schemes, and
  runtime/release activation.

## Success Criteria

- Valid lifecycle events round-trip unchanged after restart.
- A misbound project/event, malformed payload, non-integral sequence/version or
  invalid timestamp fails closed before callers receive the event.
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

- 2026-08-05 05:02:30: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05: Codex direct execution selected; no external provider or
  sub-agent dispatch.
