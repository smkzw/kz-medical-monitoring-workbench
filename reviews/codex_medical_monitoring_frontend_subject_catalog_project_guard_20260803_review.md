# Codex Review: medical_monitoring_frontend_subject_catalog_project_guard_20260803

Date: 2026-08-03 (Asia/Shanghai)
Delegated-agent output: none; route recorded but not dispatched.

## Verdict

PASS for the bounded offline project-identity guard. Not browser, scientific, UAT, or commercial acceptance.

## Boundary Check

- Only `frontend/src/App.jsx` and `tests/test_frontend_timeline_contract.py` changed.
- The backend canonicalization and source manifest were read-only evidence; no service, provider, browser, API login, runtime, SQLite or real project was started.
- No B6/C14/CAS/source-token or migration state changed; 8911/5174 remain stopped.

## Codex Verification

- Subject-catalog response now returns early when `data.project_id !== monitoringResponseProjectIdRef.current`.
- The guard uses the canonical active-project ref, preserving `my009_uc_monitoring_raw` → `proj_my009_uc` alias behavior.
- Frontend/timeline/manifest tests: **54 passed**, 17 existing warnings in 1.58s.
- `node --test frontend/src/features/medical-monitoring/*.test.mjs`: **22 suites passed**.
- `npm run build` in `frontend`: passed; existing large-chunk advisory only.
- `.venv/bin/python -m ruff check tests/test_frontend_timeline_contract.py`: passed.

## Delegated-Agent Output Review

No delegated output was used. Direct Codex traced the backend alias contract, applied the smallest state-boundary guard, and verified it.

## Residual Risk

The browser-level race, catalog shape and scientific display still require controlled Playwright verification after B6 formal review, CAS/source-token replay and approved-input gates. The guard does not prove real user acceptance or release readiness.

## Hermes workflow review

Workflow guard initialization and route recording are present; no external runner was launched. Review-gate is a record-integrity check only.
