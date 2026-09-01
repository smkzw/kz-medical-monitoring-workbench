# Task Context: medical_monitoring_frontend_subject_fixture_isolation_20260803

Created: 2026-08-03 12:27:18 (Asia/Shanghai)
Objective: Ensure the selected monitoring subject risk path never falls back to demo subject fixtures when the fetched catalog is authoritative.
Task type: `finite_code_task`; risk `high`; direct Codex execution.

## Source Of Truth

- `frontend/src/App.jsx`, `frontend/src/features/medical-monitoring/medicalMonitoringFixtures.mjs`, and `tests/test_frontend_monitoring_contract.py`.
- App state at `App.jsx:15463` fetches and stores `monitoringSubjectCatalog`; the monitoring page invocation is the authoritative handoff.
- Existing P10 checkpoint: `context/medical_monitoring_offline_boundary_checkpoint_20260803.md`.

## Evidence Before Change

- `MonitoringPage` called `buildSubjectView(subjectProfile, selectedSubject, selectedRisk)` without the catalog.
- `buildSubjectView` defaults its fourth argument to `demoSubjects`, so a risk-detail render could display fixture metadata when the API-backed catalog was absent or delayed.
- The application-level `page` builder already passed `monitoringSubjectCatalog` to subject timeline/profile views; the risk-detail path was the inconsistent branch.

## Scope

- In scope: thread the fetched catalog through the existing `MonitoringPage` props, use it for the risk-detail subject view, and add a source-level regression contract.
- Out of scope: demo fixture definitions used by explicitly demo/legacy routes; backend/API contracts; service startup; browser login; provider dispatch; real project data; B6/C14 authority records.

## Success Criteria

- The monitoring risk-detail branch passes an explicit `subjectCatalog` and defaults only to an empty array, never to `demoSubjects`.
- The application passes `monitoringSubjectCatalog` into `MonitoringPage`.
- Focused Python contract, all 22 medical-monitoring Node suites, Vite production build, and Python Ruff check pass.
- No listener is started on 8911 or 5174, and no service/provider/browser/real-project path is invoked.

## Risk Boundaries

- This is a surgical two-source-file change; preserve the existing `demoSubjects` helper default for unrelated explicit demo consumers.
- Do not perform B6 review synthesis, CAS/source-token writes, migration, or C14 activation. Do not claim browser, scientific, UAT, or commercial acceptance.
- The delegated route recorded by the workflow guard was not dispatched; direct Codex owns implementation and verification.

## Loop Log

- 2026-08-03 12:27:18: Initialized through `hermes_workflow_guard.py init-task`; no external route dispatched.
- 2026-08-03 12:28: Source audit confirmed the omitted catalog argument at `MonitoringPage` risk-detail path and authoritative catalog state at the app layer.
- 2026-08-03 12:29: Applied only the prop/argument threading change and one static contract test.
- 2026-08-03 12:30: `tests/test_frontend_monitoring_contract.py`: 23 passed; medical-monitoring Node suites: 22 suites / all assertions passed; Vite build passed; Ruff passed for the Python contract test.
- 2026-08-03 12:31: `lsof` confirmed no listeners on 8911 or 5174. Review gate remains offline-only; B6/C14 unchanged.
- 2026-08-03 12:33–12:35: MG-K10-SAR, Ruxolitinib-AD and MY009 adapter/API contract suites: **35 passed**, 19 existing warnings; no service was started.
