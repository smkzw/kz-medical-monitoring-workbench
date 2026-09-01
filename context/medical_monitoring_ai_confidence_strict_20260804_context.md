# Task Context: medical_monitoring_ai_confidence_strict_20260804

Created: 2026-08-04 23:58:19 +0800
Objective: 禁止独立 AI claim 与字段映射 confidence 的 bool/字符串伪装，保持风险排序与医学复核提示的数值语义可信
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected route: `codex` / `codex-main` / `high`

## Source of truth

- `services/api/app/monitoring_ai_contracts.py`
- `services/api/app/monitoring_ai_service.py`
- `tests/test_monitoring_ai_repository.py`
- `tests/test_monitoring_ai_service.py`
- Current B6/C14 and real-loop gate artifacts, which remain read-only.

## Finding and scope

`MonitoringAiClaim`, provider claims, and field-mapping items declared ordinary Pydantic
`float` confidence fields. Pydantic could coerce `True`/`False` into 1.0/0.0, which would
make malformed provider output look like a valid confidence and affect candidate quality
and review ordering. The slice changes those three fields to `StrictFloat`; integer JSON
values remain accepted as numeric floats, while booleans and strings fail closed.

Out of scope: provider/runtime startup, API or browser login, Playwright, real projects,
medical review, database writes, B6/C14 activation, source-token promotion, and release.

## Verification and boundaries

- Direct confidence and existing numeric regressions: 4 passed across repository/service.
- Repository/service/risk-bridge adjacent suites: 509 passed.
- Decisive monitoring-AI/real-loop/assurance suites: 893 passed, 17 existing warnings.
- Changed Python files compile; ports 8911/5174/8910/4173 are empty.
- No service, provider, external model, browser, API login, Playwright session, real project,
  or medical authority input was started or changed.

## Next safe action

Keep B6/C14 and the real-loop manifest blocked. The next live step remains formal medical
reviewer submission of five hash-bound outcomes followed by source-token and aggregate/CAS
revalidation; engineering confidence typing does not substitute for that review.
