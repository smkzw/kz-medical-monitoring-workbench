# Task Context: medical_monitoring_api_strict_boolean_input_20260805

Created: 2026-08-05 00:49:57
Objective: Harden monitoring AI, daily-run confirmation, assurance approval booleans and supersede CAS input against Pydantic coercion while preserving explicit offline compatibility
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_ai_router.py` (`FieldMappingStartRequest`)
- `services/api/app/monitoring_daily_run_router.py` (confirmation and supersede request models)
- `services/api/app/monitoring_assurance_router.py` (rollup approval and completion request models)
- `tests/test_monitoring_ai_api.py`, `tests/test_monitoring_daily_run_router.py`, and `tests/test_monitoring_assurance_principal_route.py`
- Current P10 ledger, project completion audit, and prior strict-input slices under `records/active_slices/`, `context/`, `reviews/`, and `metrics/`.
- Current filesystem is authoritative; no runtime or real-project activation is allowed by this slice.

## Scope

- In scope: use `StrictBool` for production request fields `retry_failed`, daily confirmation `reauthenticated`, assurance `site_method_approved` and `reauthenticated`; use `StrictInt` for daily supersede `expected_version`; add route/model boundary regressions; preserve valid booleans and explicit offline compatibility.
- Out of scope: provider calls, service/API startup, browser/Playwright tests, real-project data, database migration, B6/C14 review or activation, medical conclusions, and unrelated medical-writing files.

## Success Criteria

- Malformed boolean values (`0`, `1`, `"false"`, `"true"`) receive 422 at the relevant request/model boundary without repository mutation.
- Valid `True`/`False` behavior remains green for existing retry, confirmation and assurance flows.
- Daily supersede rejects bool and numeric-string CAS values.
- Focused and adjacent monitoring-AI/daily-run/assurance tests, compile, Ruff and reserved-port checks pass.
- Evidence explicitly records this as offline source-only hardening; B6/C14 and real LOOP gates remain unchanged.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- No external model dispatch is used; Codex remains final authority.
- Do not start or connect to 8911, 5174, 8910 or 4173; do not touch runtime databases or real projects.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 00:49:57: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05 00:50: inspected remaining monitoring API booleans and found the listed retry/authentication/approval fields plus daily supersede's non-strict CAS type. Next: patch only these request boundaries and add negative regressions.
- 2026-08-05 00:52: strict request fields and boundary regressions were added. Focused 117, adjacent 684, and decisive 981-test groups passed; compile, Ruff and reserved-port checks passed. No runtime/provider/browser/real-project action occurred.
- 2026-08-05 00:53: review and metrics prepared. Next safe action is another bounded P7/P8/P9 source-only gap; runtime remains blocked by formal B6 and source-token/CAS/identity gates.
