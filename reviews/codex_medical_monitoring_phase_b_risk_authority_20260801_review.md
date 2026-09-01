# Codex Review: medical_monitoring_phase_b_risk_authority_20260801

Date: 2026-08-01 23:08 CST
Execution: Codex direct; no Hermes route, conference, or sub-agent was used.
Changed source/test:
- `services/api/app/medical_risk_authority.py`
- `tests/test_medical_risk_authority.py`

## Verdict

**Pass for the declared offline Phase B contract slice; Phase B runtime migration is not complete.**

## Boundary Check

- Work stayed inside the workbench source/test files and task-scoped context/review/metrics records.
- No runtime database, migration version, `main.py`, `sqlite_runtime_store.py`, frontend, or medical-writing file was changed.
- No service was started; 8911 and 5174 are not listening. Unrelated PID 43191 on 18911 was observed only and not touched.
- Frozen v9-v11 and the completed v12 runtime evidence were not retried, reused, or reclassified.

## Codex Verification

- `python3 -m pytest tests/test_medical_risk_authority.py -q`: **7 passed**.
- Existing risk compatibility set (`test_monitoring_risk_contract_v2.py`,
  `test_medical_risk_repository.py`, `test_monitoring_rule_risk_bridge.py`,
  `test_monitoring_ai_risk_bridge.py`, `test_monitoring_risk_index_api.py`,
  `test_workbench_inbox.py`): **97 passed, 17 warnings**.
- `python3 -m py_compile` for the changed source/test: passed.
- `python3 -m ruff check` for the changed source/test: passed.
- Static review confirms explicit trial/site/subject identity, separate finding class,
  status, unread and disposition dimensions, immutable event payload/hash, source
  revision binding, append-only event ledger, exact duplicate replay, and stale CAS
  rejection.
- No browser/runtime/API check was run because this slice is deliberately offline and
  must not write the authority runtime before migration design is accepted.

## Direct Work Review

- The existing `MedicalRiskRepository` snapshot and `WorkbenchInboxService` disposition
  flow were read as the compatibility boundary; the new module does not silently replace
  either store or create a second runtime write path.
- `MedicalRiskAggregate.from_risk_case` requires a caller-supplied `trial_id` and a
  complete scope identity; it does not infer a missing site or subject.
- `MedicalRiskEvent` carries actor, source revision, expected version and deterministic
  payload hash. `MedicalRiskAggregate.apply` is pure and returns a new aggregate.
- The contract intentionally does not claim migration, dual-read reconciliation,
  restart persistence, UI integration, or commercial readiness.

## Residual Risk

- Existing runtime snapshots and disposition records remain separate authorities until
  the next Phase B slice designs migration and dual-read reconciliation.
- Existing `RiskCase` rows with missing or legacy identity fields cannot be admitted to
  the new aggregate without an explicit migration mapping; this is fail-closed by design.
- Event persistence, restart/recovery, old deep links, cross-project isolation, and
  project/site/subject UI rollups remain unverified and are required before the Phase B
  exit gate or any commercial claim.
