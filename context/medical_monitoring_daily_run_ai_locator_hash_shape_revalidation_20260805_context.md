# Task Context: medical_monitoring_daily_run_ai_locator_hash_shape_revalidation_20260805

Created: 2026-08-05 08:21:09
Objective: Harden daily-run AI source locator digest reads against strip/lower normalization
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_daily_run_ai_service.py`
- `tests/test_monitoring_daily_run_ai_service.py`
- Current authoritative real-loop gate and mode-coverage artifacts.

## Scope

- In scope: exact lowercase SHA-256 validation for a present raw-row source
  locator hash, preserving the intentional absence fallback and existing
  source-binding mismatch/ambiguity semantics, plus focused tests.
- Out of scope: provider/runtime/browser/API login/real-project activity,
  medical-writing data, B6/C14 review, release activation and unrelated
  daily-run rule/repository changes.

## Success Criteria

- Present locator hash values are never accepted after strip/lower rewriting;
  absent locator hash remains compatible with the single-source fallback.
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

- 2026-08-05 08:21:09: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05: Source audit found raw locator source hashes normalized with
  `strip().lower()` before daily-run AI evidence binding.
