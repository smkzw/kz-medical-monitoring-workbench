# Task Context: medical_monitoring_real_loop_acceptance_revalidation_20260803

Created: 2026-08-03 02:05:15
Objective: Add a read-only persisted JSON revalidation boundary for future Playwright/scientific real-loop acceptance evidence; keep all runtime, browser, provider, B6 and release authority blocked.
Task type: `finite_code_task`
Risk: `medium`
Selected agent route: `alibaba` / `qwen3.8-max-preview` / `xhigh`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_real_loop_acceptance.py` and
  `tests/test_monitoring_real_loop_acceptance.py` are the in-memory acceptance
  contract and its current regression surface.
- `services/api/app/monitoring_release_dossier.py`, the current release-gate
  snapshot, and the global/workspace `AGENTS.md` files define the commercial
  evidence boundary and fail-closed authority rules.
- Existing active-slice evidence is diagnostic only; no persisted real-loop
  result, Playwright session, provider result, B6 outcome or release authority
  may be inferred from it.

## Scope

- In scope: a pure Python revalidator that accepts a persisted real-loop
  acceptance JSON payload, reconstructs the canonical run/prompt objects,
  validates the existing acceptance contract, and optionally reopens a safe
  workspace-relative JSON file with byte/SHA identity checks; one blocked
  diagnostic artifact, focused tests, and task records.
- Out of scope: provider dispatch, Playwright/browser login, API/backend login,
  service/runtime/SQLite writes, real-project source access, B6/C14 changes,
  CAS/source-token migration, frontend/medical-writing edits, and any medical
  or release approval.

## Success Criteria

- Payload and file revalidation are deterministic and fail closed on malformed
  rows, missing/unsafe files, semantic/hash drift, duplicate IDs, or an
  acceptance report that is not derived from the canonical contract.
- Current workspace diagnostic reports no persisted real-loop evidence and
  remains `blocked`, `acceptance_complete=false`,
  `medical_confirmation_permitted=false`, and
  `runtime_write_permitted=false`.
- Focused and adjacent monitoring tests, Ruff/compile checks, and the Hermes
  review-gate pass; protected frontend hashes and 8911/5174 listener state are
  unchanged.

## Risk Boundaries

- Only task-owned source/test/context/review/metrics/active-slice files may be
  changed. Do not write to product runtime, SQLite, source registry, frontend,
  providers, browser state, or real project folders.
- The revalidator must force read-only/non-authoritative flags and must never
  turn a fresh file identity into UAT, medical confirmation, runtime write or
  release readiness.
- This is a direct Codex implementation slice; no external runner or child
  agent is dispatched. Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-03 02:05:15: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-03: Direct Codex implementation selected after confirming the
  existing in-memory contract has no persisted-file revalidation boundary;
  external execution/browser/provider routes remain intentionally unused.
