# Task Context: medical_monitoring_batch_idempotency_replay_shape_revalidation_20260805

Created: 2026-08-05 05:56:31
Objective: Fail closed on malformed or operation-drifted monitoring batch idempotency replay rows
Task type: `finite_code_task`
Risk: `high`
Selected agent route: `alibaba` / `qwen3.8-max` / `xhigh`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_batch_repository.py` (batch mutation
  idempotency storage/replay and BatchRecord result contracts).
- `tests/test_monitoring_batch_repository.py` plus batch service/diff/rule,
  field-profiler, daily-run, gold-case, mapping-lifecycle and API suites.
- Current filesystem state and
  `records/active_slices/medical_monitoring_goal_p10_20260730/LOOP_LEDGER.md`.
- Real-loop and release gate records remain authoritative and blocked; this
  slice is source-only and cannot activate runtime or external providers.

## Scope

- In scope: require the persisted idempotency operation to match the replaying
  operation; parse response JSON as an object; require a batch object bound to
  the requested project; preserve create/derived/mutation replay semantics and
  add two SQLite tamper regressions.
- Out of scope: services, ports, browsers/Playwright, API login, real project
  data, external providers, medical judgments, schema migrations,
  runtime/release activation and B6/C14 authority changes.

## Success Criteria

- Valid create, derived-snapshot and mutation idempotent replays remain
  unchanged.
- Operation drift, malformed response JSON/root or cross-project batch payload
  fails closed before a replay result is returned.
- Focused/adjacent tests, compileall, Ruff and reserved-port checks pass; the
  evidence records exact counts, hashes, warnings and residual limits.
- Hermes review gate reports `ok: true` with no warnings/errors.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 05:56:31: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05: Codex direct source-only implementation selected; no Hermes
  execution session, provider call or sub-agent dispatch.
- 2026-08-05: Hardened batch idempotency replay operation/response/project
  checks and added two isolated SQLite tamper regressions. Focused 48 passed;
  adjacent 131 passed in 80.09s; compileall/Ruff passed; reserved ports
  remained free.
- **Residual/next**: idempotency response integrity does not prove source,
  mapping, provider, clinical, browser, formal B6, C14 or commercial-release
  readiness. Keep runtime gates closed and proceed only with another bounded
  structural source-only gap.
