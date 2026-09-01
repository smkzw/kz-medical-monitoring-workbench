# Task Context: medical_monitoring_ai_router_hash_shape_revalidation_20260805

Created: 2026-08-05 08:17:38
Objective: Harden independent-AI router profile digest requests and persisted status/adoption comparisons against normalization
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_ai_router.py`
- `services/api/app/monitoring_ai_service.py`
- `tests/test_monitoring_ai_api.py`
- Current authoritative real-loop gate and mode-coverage artifacts.

## Scope

- In scope: exact lowercase SHA-256 request validation for mapping assemble/
  adopt boundaries and source-preserving persisted profile hash comparisons in
  router status, legacy compatibility and adoption paths, plus focused tests.
- Out of scope: provider/runtime/browser/API login/real-project activity,
  medical-writing data, B6/C14 review, release activation and unrelated route
  behavior.

## Success Criteria

- Noncanonical present profile/input digests are rejected or skipped closed;
  no `strip()`/`lower()` rewrite is used to match a job.
- Valid existing mapping status/adoption behavior remains compatible.
- Focused/adjacent source tests, compileall, guard preflight and review gate
  pass; reserved ports remain empty.

## Risk Boundaries

- The authoritative gate is `read_only`/`blocked`; do not start services or
  ports 8911/5174/8910/4173, call providers, use browser/Playwright or API
  login, touch real projects/medical-writing data, or perform B6/C14/release
  activation.
- This is Codex direct work; no Hermes dispatch or subagent is needed.
- Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 08:17:38: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05: Source audit found router-level profile digest comparisons still
  used normalization after the service-layer shape revalidation.
