# Codex Review: medical_monitoring_frontend_subject_fixture_isolation_20260803

Date: 2026-08-03 (Asia/Shanghai)
Delegated-agent output: none; the Hermes route was recorded but not dispatched.

## Verdict

PASS for the scoped offline source contract. This is not a browser, scientific, UAT, or commercial acceptance verdict.

## Boundary Check

- Only the requested in-scope files changed: `frontend/src/App.jsx` and `tests/test_frontend_monitoring_contract.py`.
- No backend, library, service, runtime, provider, browser, source-token, CAS, or real-project path was changed or started.
- `lsof` showed no listeners on ports 8911 or 5174; the unrelated 8900 boundary was not touched.
- Existing `demoSubjects` defaults remain for explicit demo/legacy consumers; only the real monitoring risk path was isolated.

## Codex Verification

- `App.jsx` now declares `subjectCatalog = []` on `MonitoringPage` and calls `buildSubjectView(subjectProfile, selectedSubject, selectedRisk, subjectCatalog)`.
- The app passes `subjectCatalog={monitoringSubjectCatalog}` at the monitoring page boundary.
- `.venv/bin/python -m pytest -q tests/test_frontend_monitoring_contract.py`: **23 passed**.
- `node --test frontend/src/features/medical-monitoring/*.test.mjs`: **22 suites passed** (all reported assertions passed).
- `npm run build` in `frontend`: Vite production build passed; only the existing large-chunk advisory was emitted.
- `.venv/bin/python -m ruff check tests/test_frontend_monitoring_contract.py`: passed.
- `.venv/bin/python -m pytest -q tests/test_mgk10_sar_monitoring_service.py tests/test_rux_monitoring_service.py tests/test_my009_monitoring_service.py`: **35 passed**, 19 existing warnings in 121.83s; this was in-process adapter/TestClient evidence, not a started service.
- Cross-surface frontend contract set (monitoring/timeline/unified-risk/safety projection): **65 passed**.

## Delegated-Agent Output Review

- No delegated output exists to treat as acceptance evidence. Direct Codex inspected the source, selected the narrow fix, applied it, and ran the decisive offline checks.
- The change addresses the observed propagation path without changing risk ranking, data authority, or API behavior.

## Residual Risk

- The API-backed catalog and late-loading behavior still require controlled Playwright/scientific verification after B6 formal review, aggregate/CAS replay, source-token revalidation, and approved-input issuance.
- App ownership/baseline drift noted by the prior audit remains unresolved; no rollback or broad semantic cleanup was attempted.
- The full Python suite and real-project E2E loop are not claimed here; one unrelated medical-writing test remains dependent on local oMLX translator availability.
