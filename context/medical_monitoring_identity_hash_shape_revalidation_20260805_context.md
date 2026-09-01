# Task Context: medical_monitoring_identity_hash_shape_revalidation_20260805

Created: 2026-08-05 07:36:11
Objective: Harden the offline monitoring identity and permission boundary so optional signature evidence and required server verification reference hashes reject padded, uppercase, non-string, or malformed values without normalization, with focused source-only regressions.
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_identity_authorization.py`
- `services/api/app/monitoring_runtime_principal.py`
- `tests/test_monitoring_identity_authorization.py`
- `tests/test_monitoring_runtime_principal.py`
- Current P10/B6/C14 gate records; the real-loop gate remains read-only and
  blocked.

## Scope

- In scope: exact lowercase SHA-256 shape validation for signature evidence
  tokens and required server verification-reference digests; focused negative
  tests and source-only evidence.
- Out of scope: authentication/provider integration, signature verification,
  router wiring, persistence/audit writes, browser/API login, real projects,
  medical-writing data, B6/C14 activation and release claims.

## Success Criteria

- Padded, uppercase, non-string and malformed values fail closed without
  normalization; valid lowercase values retain current behavior.
- Existing authorization, runtime-principal and route-context regressions
  remain green; compile-only check passes and all reserved ports remain empty.
- No provider, service, browser, real-project or runtime evidence is created.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- Keep the authoritative gate read-only/blocked and do not start 8911, 5174,
  8910 or 4173.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 07:36:11: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05 07:36-07:40: Strict identity hash validation and focused negative
  regressions were added. Focused **31 passed**; authorization/runtime
  adjacency **153 passed**; compileall passed; Ruff unavailable; ports empty;
  preflight and review-gate passed.
- 2026-08-05 07:40-07:41: Explicit non-real P9 composite covering clinical
  handoff/projection, assurance/release, identity/route authorization,
  daily-run boundaries, and medical-writing protection consumers passed **324
  tests, 17 warnings** in 19.84s; `real_` tests were excluded. No runtime,
  provider, browser, API-login or real-project action occurred.
