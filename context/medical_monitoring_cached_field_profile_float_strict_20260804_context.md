# Task Context: medical_monitoring_cached_field_profile_float_strict_20260804

Created: 2026-08-04 23:58:19 +0800
Objective: 收紧缓存 field-profile `null_rate` 的有限数值解析，禁止 bool/字符串/非有限值污染独立 AI 字段画像
Task type: `code_scoped_patch_plan`
Risk: `medium`
Selected route: `codex` / `codex-main` / `high`

## Finding and scope

`MonitoringFieldProfileSnapshot.from_dict` used `float()` for `null_rate`. A boolean could be
normalized to 0.0/1.0 and a non-finite or out-of-range value was not rejected at this boundary.
The slice adds `_required_float`, which accepts JSON integers/floats only, rejects bool and
strings, requires finiteness, and enforces the valid 0–1 null-rate range.

Source of truth: `services/api/app/monitoring_ai_field_profiler.py`, its field-profiler tests,
and the current read-only B6/C14/real-loop gate artifacts. Out of scope: runtime/provider/
browser/API login, Playwright, real projects, medical review, database writes, gate activation,
source-token promotion, and release.

## Verification and boundaries

- Focused field-profile/cache tests: 6 passed; complete field-profiler file: 18 passed.
- Field-profiler/service/repair adjacent suites: 478 passed.
- Decisive monitoring-AI/real-loop/assurance suites: 893 passed, 17 existing warnings.
- Full monitoring Python glob after the slice: 2150 passed, 25 warnings in 494.65s.
- Changed Python files compile; ports 8911/5174/8910/4173 are empty.
- No service, provider, external model, browser, API login, Playwright session, real project,
  or medical authority input was started or changed.

## Next safe action

Keep B6/C14 and the real-loop manifest blocked. Only formal reviewer outcomes followed by
source-token and aggregate/CAS revalidation can change the live path; this offline parser fix
does not substitute for medical approval.
