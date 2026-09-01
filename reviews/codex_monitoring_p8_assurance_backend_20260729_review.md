# Review: monitoring_p8_assurance_backend_20260729

**Status:** Codex accepted for the authorized P8 backend slice on 2026-07-30.

## Main-Venue Resolution

The previously recorded residual risk that runtime construction lacked a
`risk_reader` is resolved:

- `create_medical_risk_reference_reader()` reads the pinned snapshot from the
  existing `MedicalRiskRepository`, scoped by `project_id`.
- It projects only the minimum `RiskReference` fields needed by assurance:
  risk identities, scope, category, severity/status, batch delta, Safety/PV
  flag, CM/study-treatment boundary flags, and closure-evidence availability.
- It does not copy titles, rationale, evidence fragments, or other persisted
  medical-risk facts into the assurance repository.
- It fails closed on a missing/cross-project pinned snapshot and when the
  project's current risk snapshot has drifted from the task's pinned snapshot.
- `main.py` injects this reader into `MonitoringAssuranceService`.

## Verified Boundaries

- Pinned real risk snapshot produces subject/site/trial rollups with identical
  risk-instance sets.
- A later risk snapshot causes rollup generation to return HTTP 409 with
  `assurance_drift_detected`.
- Cross-project task access returns 404; cross-project snapshot reads fail
  closed.
- Safety/PV remains an additional dimension.
- CM risk and study-treatment change risk remain mutually distinct and are
  counted separately.
- Site clustering remains `descriptive_only` when no project-approved method
  exists.
- Public assurance storage and responses contain references, not duplicated
  risk facts.

## Acceptance Evidence

- `python3 -m pytest -q tests/test_monitoring_assurance.py`
  - 21 passed.
- System-`python3` combined regression:
  - `tests/test_monitoring_assurance.py`
  - `tests/test_medical_monitoring_module_contract.py`
  - `tests/test_monitoring_risk_index_api.py`
  - `tests/test_monitoring_daily_run_router.py`
  - Result: 45 passed, 10 existing FastAPI `on_event` deprecation warnings.
- Python compilation passed for the modified service, `main.py`, and focused
  test file.
- Ruff E/F passed for the modified P8 service and focused test file.

The earlier statement that main-import tests could not run because of a
`cryptography` dependency was incorrect and is superseded by the successful
system-`python3` regression above.

## Operational Boundary

The running API process was not restarted and the real runtime database was not
modified, as required. Main construction and API behavior were instead verified
against isolated temporary SQLite runtime state.
