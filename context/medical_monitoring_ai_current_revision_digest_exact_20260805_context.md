# Task Context: medical_monitoring_ai_current_revision_digest_exact_20260805

Created: 2026-08-05 09:59:39
Objective: Reject non-canonical persisted AI field-profile digests when recomputing the current listing revision
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_ai_router.py`, specifically
  `_current_revision_for_job()` for persisted field-profile reconstruction.
- `tests/test_monitoring_ai_api.py` focused API/router regressions.
- `context/medical_monitoring_p9_source_only_checkpoint_20260805.md` and
  `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json`
  for the active P9 boundary and blocked P10 gate.

## Scope

- In scope: reject non-string, padded, uppercase or malformed persisted
  `field_profile.profile_sha256` while recomputing a listing job's current
  revision; fail closed for malformed profile roots/batch ids; add focused
  regression coverage; run the AI source suites and compile checks.
- Out of scope: provider/runtime/browser/API login/real-project activity,
  authentication or authorization redesign, schema migration, medical-writing
  data, B6/C14 review, release activation and clinical/commercial claims.

## Success Criteria

- A padded profile digest cannot become a valid revision through `.strip()`;
  malformed persisted profile data returns an unavailable revision (`""`).
- Valid existing mapping status/recovery behavior remains compatible.
- Focused API tests, all discovered non-`real_` AI source suites, compileall and
  review-gate pass; reserved ports remain stopped.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- This is an offline read-shape repair, not evidence of a valid provider,
  runtime identity, authorization decision or clinical result.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 09:59:39: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05 10:00: Source audit found `_current_revision_for_job()` still
  used `str(...).strip()` for persisted `profile_sha256`; padded values could
  be silently converted into a canonical digest before revision computation.
- 2026-08-05 10:01: Added strict persisted profile-root/digest reads and four
  negative regressions (leading/trailing whitespace, uppercase and non-string).
  Focused API suite: **27 passed**; selected revision subset: **5 passed**.
- 2026-08-05 10:02: All discovered `tests/test_monitoring_ai*.py` source suites
  with `real_` excluded: **796 passed, 4 deselected, 17 warnings** in 14.61s;
  compileall passed; Ruff is unavailable. No runtime, service, port, browser,
  provider or real project was started.

## Source digests at checkpoint

- `services/api/app/monitoring_ai_router.py`:
  `434a09cd723d6a1f6aceee838a99703ae873a74e64879b76f660c5f9209cfa63`
- `tests/test_monitoring_ai_api.py`:
  `1a2a19dbe68f73d46d801f39a14c8b30339db668e06c78313722b110fb3dbd98`
