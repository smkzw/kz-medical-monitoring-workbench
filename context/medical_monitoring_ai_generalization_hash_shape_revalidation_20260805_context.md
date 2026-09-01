# Task Context: medical_monitoring_ai_generalization_hash_shape_revalidation_20260805

Created: 2026-08-05 07:56:09
Objective: Harden anti-overfit generalization evidence hash validators to reject noncanonical present digests without normalization
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_ai_generalization.py`
- `tests/test_monitoring_ai_generalization.py`
- `services/api/app/monitoring_ai_contracts.py` (canonical digest helper)
- Current P10/B6/C14 gate records; the real-loop gate remains read-only and
  blocked.

## Scope

- In scope: exact lowercase SHA-256 validation for profile, observation
  snapshot and profile snapshot hashes in the anti-overfit generalization
  evidence contract; focused and adjacent source-only regressions.
- Out of scope: changing structure-class semantics, project coverage logic,
  provider/runtime/browser activation, real projects, medical-writing data,
  B6/C14 or release claims.

## Success Criteria

- Present malformed, padded, uppercase, non-hex, short or non-string hashes fail
  closed; valid lowercase values remain unchanged.
- Existing profile/evidence completeness, fingerprint and issue behavior stays
  green; compile and focused/adjacent tests pass.
- No service, provider, browser, API login, runtime or real project action.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- Keep 8911, 5174, 8910 and 4173 stopped; do not use Playwright or real data.
- Do not weaken anti-overfit coverage or infer structure classes from project
  names/listings.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 07:56:09: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05: Reconnaissance found `_clean_sha256` using `str(...).strip().lower()`
  for profile and generalization snapshot evidence; this is a concrete
  source-preserving integrity gap adjacent to the AI contract repair.
- 2026-08-05: Replaced normalization with exact lowercase 64-hex validation
  using a `\Z` end boundary; added malformed-shape regressions. Focused
  generalization **12 passed**; all discovered AI-contract tests with `real_`
  excluded **765 passed, 4 deselected, 17 warnings**; compileall and preflight
  passed; reserved ports empty; Ruff unavailable.
