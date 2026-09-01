# Task Context: medical_monitoring_ai_evidence_source_shape_20260804

Created: 2026-08-04 20:08:35
Objective: Harden P4 AI evidence source declarations against implicit type coercion before hash-bound revalidation
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_ai_evidence_revalidation.py` — P4 persisted
  source declaration parser and hash-bound revalidation.
- `tests/test_monitoring_ai_evidence_revalidation.py` — deterministic source
  shape/drift/authority regression contract.
- `records/active_slices/medical_monitoring_release_evidence_coverage_20260802/CURRENT_RELEASE_COVERAGE.json`
  — current blocked coverage fixture; it is read-only input, not a release
  authority source.

## Scope

- In scope: strict shape validation for declared source `id`, `path`, `bytes`,
  `sha256`, and optional `role`; focused regression tests and evidence.
- Out of scope: changing source files, coverage status, P4 artifacts, provider
  calls, AI activation, SQLite, API routes, browser/Playwright, real projects,
  B6/C14, medical-writing, or release authority.

## Success Criteria

- Non-string IDs/paths/roles/SHA values and non-integer or boolean byte counts
  are rejected as `coverage_shape_invalid`; no implicit `str()`/`int()` cast
  can turn malformed source declarations into a hash-bound source.
- Existing valid declarations retain the same source-count, byte/hash drift,
  and blocked-authority behavior.
- Focused and adjacent tests pass; changed Python compiles; Hermes review-gate
  passes with verification required.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- Direct Codex owns verification and acceptance; no delegated agent or external
  provider is used.
- Keep the current release coverage artifact blocked and read-only; do not infer
  P4 evidence or grant any permission from this slice.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 20:08:35: Task initialized by `tools/hermes_workflow_guard.py init-task`.
