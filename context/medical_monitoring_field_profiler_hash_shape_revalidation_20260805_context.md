# Task Context: medical_monitoring_field_profiler_hash_shape_revalidation_20260805

Created: 2026-08-05 07:59:02
Objective: Harden persisted field-profile snapshot digest validation to reject noncanonical hashes without normalization
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_ai_field_profiler.py`
- `tests/test_monitoring_ai_field_profiler.py`
- `services/api/app/monitoring_ai_field_profile_cache.py` and its existing cache
  identity tests (adjacent contract only)
- Current P10/B6/C14 gate records; the real-loop gate remains read-only and
  blocked.

## Scope

- In scope: exact lowercase SHA-256 validation for persisted field-profile
  snapshot input/profile/source-binding digests; focused and adjacent
  source-only regressions.
- Out of scope: field inference, mapping semantics, batch persistence schema,
  provider/runtime/browser activation, real projects, medical-writing data,
  B6/C14 and release claims.

## Success Criteria

- Present uppercase, padded, malformed, short, non-hex or non-string snapshot
  hashes fail closed without normalization.
- Valid lowercase snapshot/cache identity behavior remains green; compile and
  focused/adjacent tests pass with no runtime/provider/browser action.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- Keep 8911, 5174, 8910 and 4173 stopped; do not use Playwright or real data.
- Do not alter field-profile inference or cache key semantics beyond rejecting
  noncanonical persisted digest text.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 07:59:02: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05: Reconnaissance found `_required_digest` still using
  `str(...).strip().lower()` in the persisted field-profile snapshot reader,
  despite the adjacent cache-identity repair; this is a concrete read-shape
  integrity gap.
- 2026-08-05: Replaced the normalizer with exact lowercase 64-hex validation
  and added persisted snapshot tamper regressions. Focused profiler **19
  passed**; batch/profiler adjacency **99 passed, 5 deselected, 17 warnings**;
  compileall and corrected preflight passed; reserved ports empty; Ruff
  unavailable.
