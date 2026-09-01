# Task Context: medical_monitoring_frozen_mapping_hash_read_shape_revalidation_20260805

Created: 2026-08-05 06:45:34
Objective: Harden frozen monitoring mapping hash read shape and canonical identity without runtime activation
Task type: `finite_code_task`
Risk: `high`
Selected agent route: `alibaba` / `qwen3.8-max` / `xhigh`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_batch_repository.py` (`load_frozen_mapping_contract`)
- `tests/test_monitoring_batch_repository.py` (frozen mapping contract lifecycle/tamper coverage)
- Current filesystem and the active read-only gate; no runtime or real-project data is in scope.

## Scope

- In scope: preserve-and-validate lowercase repository/mapping identity SHA-256 values during frozen mapping reads; add one persisted uppercase repository-hash regression.
- Out of scope: mapping schema redesign, clinical mapping decisions, runtime activation, services/ports, browser/Playwright, providers, real projects, B6/C14 and commercial-release claims.

## Success Criteria

- Uppercase/non-canonical frozen mapping hashes fail closed instead of being lowercased.
- Existing v1/v2 mapping contract and batch lifecycle tests remain green.
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

- 2026-08-05 06:45:34: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05: Frozen mapping contract reads now reject non-canonical uppercase repository and mapping identity hashes; added an uppercase repository-hash tamper regression. Focused batch suite: 50 passed in 0.94s. Filtered adjacent batch/mapping suite: 106 passed, 5 deselected in 2.17s (`real_` excluded). Compileall and Ruff passed; ports 8911/5174/8910/4173 are empty.
