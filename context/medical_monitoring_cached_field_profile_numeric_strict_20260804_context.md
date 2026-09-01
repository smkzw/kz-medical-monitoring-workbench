# Task Context: medical_monitoring_cached_field_profile_numeric_strict_20260804

Created: 2026-08-04 23:58:19 +0800
Objective: 收紧缓存 field-profile 快照的数值解析，禁止 bool/字符串通过 int() 伪装成计数或版本并进入独立 AI 输入
Task type: `code_scoped_patch_plan`
Risk: `medium`
Selected route: `codex` / `codex-main` / `high`

## Source of truth

- `services/api/app/monitoring_ai_field_profiler.py`
- `tests/test_monitoring_ai_field_profiler.py`
- Existing B6/C14/current-real-loop and release gate artifacts; these remain read-only.

## Scope and finding

The cached `MonitoringFieldProfileSnapshot.from_dict` path used `int()` for row counts,
relationship counts, frequency counts, anomaly lengths, batch revision, and row count.
Python booleans could therefore be accepted as 0/1 after cache bytes and semantic digest
were replayed. The slice adds one strict integer loader and applies it to all cached numeric
metadata, retaining non-negative/positive bounds.

Out of scope: provider/runtime startup, database mutation, API or browser login, Playwright,
real projects, medical review, B6/C14 activation, source-token promotion, and release.

## Verification and boundaries

- Focused cache/profile regressions: 6 passed (5 cache tests plus the new strict metadata test).
- Field-profiler/service/repair adjacent suites: 477 passed.
- Decisive monitoring-AI/real-loop/assurance suites: 891 passed, 17 existing warnings.
- Changed Python files compile; ports 8911/5174/8910/4173 are empty.
- No service, provider, external model, browser, API login, Playwright session, real project,
  or medical authority input was started or changed.

## Next safe action

Keep B6/C14 and the real-loop manifest blocked. Continue only with a separately justified
offline contract gap; the next real-loop action still requires the existing refresh packet and
five formal medical reviewer outcomes, not another engineering-only artifact.
