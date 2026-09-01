# Task Context: medical_monitoring_phase_b2_reconciliation_20260801

Created: 2026-08-01 23:10:04
Objective: Build and verify a read-only reconciliation and migration-mapping contract between existing RiskCase/snapshot records and disposition records, detecting identity gaps, orphan or mismatched dispositions, duplicate/chain conflicts, and aggregate state drift without runtime writes.
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `reviews/medical_monitoring_system_retro_roadmap_20260801.md` Phase B B2 scope.
- `services/api/app/medical_risk_authority.py` B1 identity/aggregate/event contract.
- `packages/contracts/workbench_contracts/models.py` `RiskCase` and `RuxRiskDispositionRecord`.
- `services/api/app/medical_risk_repository.py` snapshot/risk history semantics.
- `services/api/app/workbench_inbox.py` source-version and disposition projection semantics.
- `services/api/app/sqlite_runtime_store.py` append-only disposition storage and stale-state rejection.
- Current filesystem is authoritative; reconciliation is read-only and must not migrate any runtime database.

## Scope

- In scope: pure reconciliation and migration-mapping report for `RiskCase`/`MedicalRiskAggregate` rows and `RuxRiskDispositionRecord` rows; identity, source-version, orphan, duplicate and state-chain diagnostics; focused tests and review records.
- In scope: explicit mapping inputs for trial identity and expected source versions; fail closed when mapping evidence is absent.
- Out of scope: reading or writing live service state, schema migration, dual-write, router/frontend changes, real-project execution, or medical-writing changes.

## Success Criteria

- Clean records produce a deterministic zero-issue report and stable counts.
- Missing trial/site/subject/risk identity is reported as a migration blocker rather than inferred.
- Orphan dispositions, risk-instance mismatch, source-version mismatch, duplicate business events, disposition chain gaps and aggregate-state drift are distinct issue codes.
- Report output is deterministic, JSON-safe and contains enough locators to plan a versioned migration without mutating input records.
- Focused tests and the existing risk compatibility set pass; no service is started and no runtime database is changed.

## Risk Boundaries

- Only source/test files inside this workbench plus task-scoped context/review/metrics records may change.
- Do not modify `main.py`, `sqlite_runtime_store.py`, runtime databases, migration versions, frontend, or medical-writing files.
- Do not start 8911/5174 or touch 18911; frozen v9-v12 jobs remain untouched.
- Codex is the sole execution and acceptance authority; no Hermes/external route or sub-agent is used.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-01 23:10:04: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-01 23:10: B1 contract and existing runtime disposition semantics selected as read-only reconciliation boundary; absent trial/source mapping must be reported, not inferred.
- 2026-08-01 23:16: Added `services/api/app/medical_risk_reconciliation.py`, focused regressions, and a read-only clone evidence script. Static and compatibility checks passed.
- 2026-08-01 23:16: Actual A6 clone report loaded latest RUX/MY009 snapshots (35 risk rows) and 5 disposition rows; all 5 dispositions are blocking identity mismatches, so `migration_ready=false`. No source DB write occurred.

## Closure And Next Safe Action

- B2 read-only reconciliation is complete; it is a blocker report, not a migration.
- Before any dual-read or versioned migration, create an explicit legacy mapping review for the three MY009 records (legacy `risk_id` without current `risk_instance_id`/`risk_key`) and two RUX records (same risk key but old instance), then rerun this report with approved mappings.
- The next task may design a mapping-only adapter and dry-run remap; it must not write or delete old records, alter runtime schema, or start services until the mapping is independently reviewed.
