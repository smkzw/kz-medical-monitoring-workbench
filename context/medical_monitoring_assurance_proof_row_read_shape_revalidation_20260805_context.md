# Task Context: medical_monitoring_assurance_proof_row_read_shape_revalidation_20260805

Created: 2026-08-05 07:25:09
Objective: Harden persisted monitoring assurance proof row read shape without runtime activation
Task type: `finite_code_task`
Risk: `high`
Selected agent route: Codex direct; no delegated provider or sub-agent is permitted for this slice.

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_assurance_repository.py`, persisted proof reader
  `_proof_from_row`, and assurance/proof tests.
- Current filesystem and the read-only real-loop gate under `records/active_slices/`.
- Do not read/write real-project data, start a service/browser, invoke a
  provider, or alter product surfaces outside the scoped source/test files.

## Scope

- In scope: exact text validation for persisted proof row identity and payload
  JSON shape; one padded-project tamper regression; non-runtime assurance tests,
  compileall, port checks and evidence.
- Out of scope: proof semantic policy changes, rollup/audit behavior, schema or
  API/UI changes, external models, browser/Playwright, service startup, real
  projects, B6/C14 activation and commercial release claims.

## Success Criteria

- Padded/non-string proof row identities fail closed while valid proof content
  hash and lifecycle behavior remain intact.
- Focused assurance/principal tests pass; compileall passes; reserved ports are
  empty; review gate has no warnings/errors.

## Risk Boundaries

- Only scoped source/test/evidence files may change. Keep runtime activation
  read-only/blocked; no provider, sub-agent, browser, login or real-project
  operation is allowed.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 07:25:09: Task initialized by `tools/hermes_workflow_guard.py init-task`.
