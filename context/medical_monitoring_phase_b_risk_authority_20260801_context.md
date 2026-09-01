# Task Context: medical_monitoring_phase_b_risk_authority_20260801

Created: 2026-08-01 23:02:00
Objective: Implement and verify the offline MedicalRiskAggregate, append-only MedicalRiskEvent, explicit trial/site/subject identity, finding-class separation, and compare-and-swap conflict contract without changing runtime schemas or starting services.
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `reviews/medical_monitoring_system_retro_roadmap_20260801.md` Phase B contract.
- `services/api/app/medical_risk_repository.py` snapshot/risk history authority.
- `services/api/app/workbench_inbox.py` current monitoring projection and disposition workflow.
- `services/api/app/sqlite_runtime_store.py` current append-only disposition/CAS/idempotency implementation.
- `packages/contracts/workbench_contracts/models.py` existing `RiskCase`, risk status, and disposition request/record contracts.
- `tests/test_monitoring_risk_contract_v2.py`, `tests/test_medical_risk_repository.py`, and related monitoring risk tests.
- Current filesystem is authoritative; no runtime database or service is to be changed in this offline slice.

## Scope

- In scope: introduce a pure, versioned authority contract for explicit trial/site/subject risk identity, finding-class separation, immutable append-only events, and CAS state transitions; add focused regressions and source review.
- In scope: prove compatibility mapping from the existing `RiskCase` without changing existing runtime schema, routers, repositories, migration versions, or frontend behavior.
- Out of scope: runtime DB migrations, dual-write removal, service startup, API changes, frontend changes, real-project execution, or modification of the medical-writing subsystem.

## Success Criteria

- `MedicalRiskAggregate` requires explicit identity and keeps trial/site/subject scope unambiguous.
- `risk`, `prompt`, `registered_finding`, `rescue_or_exempt`, `not_applicable`, and `uncertain` remain distinct finding classes.
- `MedicalRiskEvent` is immutable, references the aggregate identity and source revision, and has deterministic payload identity.
- Event application uses expected aggregate version and rejects stale writes without mutating state; duplicate event IDs are idempotent only for an identical event.
- Read/disposition/reopen/query-draft transitions preserve the risk fact and disposition state as separate dimensions.
- Focused tests plus existing risk contract/repository/bridge tests pass; no service is started and no production database is modified.

## Risk Boundaries

- Only source and test files inside this workbench plus this task's context/review/metrics records may change.
- Do not write to runtime databases, migration schemas, `main.py`, `sqlite_runtime_store.py`, frontend, or medical-writing paths in this slice.
- Do not start 8911/5174 or touch unrelated 18911; do not retry or reuse frozen v9-v11 jobs.
- Codex is the sole execution and acceptance authority; no Hermes/external route or sub-agent is used.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-01 23:02:00: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-01 23:05: Source inventory confirmed existing snapshot authority and a separate disposition store; Phase B slice will add the missing pure aggregate/event/CAS contract before any runtime integration.
- 2026-08-01 23:08: Added `services/api/app/medical_risk_authority.py` and focused contract regressions. The contract is pure/offline: explicit trial/site/subject identity, six finding classes, immutable event payload/hash, source binding, append-only ledger, exact replay and stale CAS conflict.
- 2026-08-01 23:08: Verification passed: focused 7 tests; existing risk compatibility set 97 tests; pycompile and Ruff check passed. No service or runtime database was touched.

## Closure And Next Safe Action

- This checkpoint closes only Phase B B1 (offline authority contract), not Phase B or the project Goal.
- Next: design a read-only adapter/reconciliation report for existing `MedicalRiskRepository` snapshots and `RuxRiskDispositionRecord`/runtime disposition records, including legacy identity gaps, orphan/mismatch/duplicate categories and a no-write migration plan.
- Only after that report and focused tests pass may a separate task authorize dual-read or versioned migration. Do not add runtime dual-write, start services, or change frontend projections in the current checkpoint.
