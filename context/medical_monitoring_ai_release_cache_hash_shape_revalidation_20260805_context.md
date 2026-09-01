# Task Context: medical_monitoring_ai_release_cache_hash_shape_revalidation_20260805

Created: 2026-08-05 08:01:50
Objective: Harden independent-AI release and field-profile cache digest validators to reject noncanonical values without normalization
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_ai_release.py`
- `services/api/app/monitoring_ai_release_gate.py`
- `services/api/app/monitoring_ai_field_profile_cache.py`
- `tests/test_monitoring_ai_release.py`
- `tests/test_monitoring_ai_release_gate.py`
- `tests/test_monitoring_ai_field_profiler.py`
- Current P10/B6/C14 gate records; the real-loop gate remains read-only and
  blocked.

## Scope

- In scope: exact lowercase SHA-256 validation for AI prompt/model release
  evidence, optional generalization snapshot evidence and field-profile cache
  manifest/snapshot bindings; focused/adjacent source-only regressions.
- Out of scope: release approval/activation behavior, provider/runtime/browser
  activation, field inference, real projects, medical-writing data, B6/C14 and
  commercial-release claims.

## Success Criteria

- Present malformed, padded, uppercase, short, non-hex or non-string digest
  values fail closed; the intentionally empty optional approval/generalization
  fields remain compatible when semantically absent.
- Existing valid release, gate and cache behavior remains green; compile and
  focused/adjacent tests pass without runtime/provider/browser action.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- Keep 8911, 5174, 8910 and 4173 stopped; do not use Playwright or real data.
- Do not turn optional approval/generalization evidence into a new required
  field; only remove silent normalization of present values.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 08:01:50: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05: Reconnaissance found remaining `.strip().lower()` digest readers
  in AI release, release-gate optional generalization evidence and the field
  profile cache store; this is a concrete cross-boundary integrity gap.
- 2026-08-05: Replaced those normalizers with exact lowercase validators while
  preserving intentionally empty optional approval/generalization fields; added
  release/gate/cache regressions. Focused **53 passed**; all AI-contract tests
  with `real_` excluded **771 passed, 4 deselected, 17 warnings**; compileall
  and preflight passed; reserved ports empty; Ruff unavailable.
