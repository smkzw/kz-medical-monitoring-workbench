# Task Context: medical_monitoring_batch_root_version_read_shape_revalidation_20260805

Created: 2026-08-05 06:42:50
Objective: Harden persisted monitoring batch root version read shape without runtime activation
Task type: `finite_code_task`
Risk: `high`
Selected agent route: `alibaba` / `qwen3.8-max` / `xhigh`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_batch_repository.py` (`_batch_from_row`)
- `tests/test_monitoring_batch_repository.py` (batch root-shape regressions)
- Current filesystem and the active read-only gate; no runtime or real-project data is authoritative for this slice.

## Scope

- In scope: remove numeric coercion from persisted batch `version` reconstruction and add one text-version tamper regression; source-only deterministic verification.
- Out of scope: batch schema/migration changes, data repair, runtime activation, services/ports, browser/Playwright, providers, real projects, B6/C14 and commercial-release claims.

## Success Criteria

- Persisted batch versions must be non-bool positive integers, not numeric strings or floats that require coercion.
- Existing batch lifecycle and adjacent mapping/diff/rule behavior remain green.
- Compileall/Ruff pass and required ports remain empty.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- Do not dispatch the guard-emitted route: authority remains read-only with provider/runtime activation forbidden. Codex performs this source-only slice directly.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 06:42:50: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05: `_batch_from_row` now rejects non-int/non-bool versions without `int()` coercion; added a non-numeric text-version regression. Focused batch suite: 50 passed in 0.91s. Filtered adjacent batch/mapping suite: 106 passed, 5 deselected in 2.11s (`real_` excluded). Compileall and Ruff passed; ports 8911/5174/8910/4173 are empty.
