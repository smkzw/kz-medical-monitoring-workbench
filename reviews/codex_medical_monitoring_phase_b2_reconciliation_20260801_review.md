# Codex Review: medical_monitoring_phase_b2_reconciliation_20260801

Date: 2026-08-01 23:16 CST
Execution: Codex direct; no Hermes route, conference, or sub-agent was used.
Changed source/test/evidence:
- `services/api/app/medical_risk_reconciliation.py`
- `tests/test_medical_risk_reconciliation.py`
- `runs/execution/medical_monitoring_phase_b2_reconciliation_20260801/run_readonly_clone_reconciliation.py`
- `runs/execution/medical_monitoring_phase_b2_reconciliation_20260801/ACTUAL_CLONE_RECONCILIATION.json`

## Verdict

**Pass for B2 read-only reconciliation and migration mapping; runtime migration is blocked by five explicit identity mismatches and was not attempted.**

## Boundary Check

- Reconciliation opened only the task-owned A6 isolated clone using SQLite `mode=ro`.
- No runtime database, schema, migration version, router, frontend, `main.py`,
  `sqlite_runtime_store.py`, or medical-writing file was changed.
- No service was started; 8911/5174 remain stopped and unrelated 18911/PID 43191 was
  not touched. Frozen v9-v12 jobs were not retried or reused.
- The generated JSON is evidence, not an authority write or migration result.

## Codex Verification

- `python3 -m pytest tests/test_medical_risk_reconciliation.py -q`: **7 passed**.
- B1 authority plus existing risk compatibility set: **104 passed, 17 warnings**.
- `python3 -m py_compile` and `python3 -m ruff check` for B1/B2 source, tests and the
  read-only evidence script: passed.
- Actual isolated clone read-only report:
  `runs/execution/medical_monitoring_phase_b2_reconciliation_20260801/ACTUAL_CLONE_RECONCILIATION.json`.
  It selected the latest snapshot per project (RUX 16 risks, MY009 19 risks), loaded
  35 canonical risk rows and 5 disposition records, and found **5 blocking
  `disposition_identity_mismatch` issues, 0 matched dispositions, migration_ready=false**.
- The three MY009 records carry a legacy `risk_id` but no matching current
  `risk_instance_id`/`risk_key`; the two RUX records point to an older risk instance
  for the same risk key. These are migration candidates, not silently matched facts.
- No browser/API/runtime check was run because B2 is explicitly read-only and a
  service-mediated reconciliation would risk writing or mutating the current stores.

## Direct Work Review

- The reconciler accepts either the B1 `MedicalRiskAggregate` or legacy `RiskCase` and
  requires explicit project→trial and `(project,risk_instance_id)→source_version`
  mappings. It reports missing mappings instead of inferring them.
- Issue codes are separate for identity gap, duplicate risk instance, orphan,
  identity mismatch, source-version mapping/mismatch, duplicate business event,
  disposition chain gap and aggregate state drift.
- Report ordering and hash are deterministic; inputs are consumed read-only and the
  report contains migration locators without exposing secrets.
- The actual clone result is intentionally not “clean”: blocking mismatches are the
  evidence needed before a future migration task.

## Residual Risk

- Five existing disposition rows cannot yet be admitted to the B1 authority without an
  explicit legacy-to-current risk-instance mapping. No mapping was guessed or written.
- The clone contains historical snapshots and current records; a production migration
  still needs a governed snapshot-selection policy, per-record mapping review, and
  restart/rollback evidence.
- Dual-read comparison, versioned migration, old deep-link behavior, frontend unified
  writes and cross-project authorization remain pending Phase B B3+.
