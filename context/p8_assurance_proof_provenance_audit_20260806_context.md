# Task Context: p8_assurance_proof_provenance_audit_20260806

Created: 2026-08-06 03:26:23; completed: 2026-08-06 (Asia/Shanghai)
Objective: Audit P8 full-recompute proof provenance and identify client-trusted fields before controlled runtime activation.
Task type: `finite_code_task`; risk: `high`
Execution: direct Codex read-only audit; guard-selected night route recorded, no provider or delegated agent dispatched.

## Source Of Truth

- `services/api/app/monitoring_assurance_service.py`: service derivation and proof handoff.
- `services/api/app/monitoring_assurance_router.py`: server-principal action route and request schema.
- `services/api/app/monitoring_assurance_repository.py`: proof persistence/strict types/hash/CAS.
- `services/api/app/main.py`: production risk-reader wiring and principal route configuration.
- `tests/test_monitoring_assurance.py`, `tests/test_monitoring_assurance_principal_route.py`: isolated proof/action contracts.
- `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json`: current runtime authority.

## Scope

- In scope: read-only trace of which proof fields are recomputed from the pinned risk snapshot, which remain caller-supplied, production wiring, persistence/CAS/audit properties, and the exact pre-activation decision gap.
- Out of scope: changing proof schemas, runtime/provider/browser/API login, real projects, SQLite/runtime data, B6/C14/source-token activation, Safety/PV or medical-writing.

## Findings

1. Production `MonitoringAssuranceService` is constructed with `create_medical_risk_reference_reader(medical_risk_repository)`, and the production router explicitly uses `principal_resolver=resolve_monitoring_principal_from_request` plus `require_server_principal=True`.
2. When the risk reader is present, the service recomputes three-level reconciliation, open-risk/open-high-risk counts and closed-risk-without-evidence counts from the pinned risk snapshot. These six values override the request payload.
3. The caller still supplies `planned_subjects`, `actual_subjects`, `planned_sites`, `actual_sites`, `critical_domains`, `planned_rules`, `actual_rules`, `per_domain_counts`, `failures`, `skips`, `retries`, `owner` and `lock_impact`. The repository enforces strict types, pinned snapshot identity, content hash, CAS and audit linkage, but does not prove that those values came from a deterministic engine run.
4. Rollup generation is fully risk-reader-derived, while proof generation has this mixed provenance. Current runtime principal/write gate is blocked, so no live write occurred; the gap must be closed before activation.

## Decision Required Before Runtime

- Preferred: a server-side deterministic evidence-run ledger generates the complete proof and the mutation accepts only an opaque run/artifact ID plus a server-verified content hash.
- Alternative: retain the mutation shape but require a signed/hashed evidence manifest with source revision, execution ID, rule/model revisions and revalidated counts; reject caller-only counts/failures/skips.
- Do not silently select either route in a routine patch; this is a high-risk evidence authority decision.

## Verification

- Static source/route/wiring inspection completed; no product source changed.
- Existing production wiring and repository contracts were cross-checked against the named tests; no runtime was started.
- Gate remains `read_only / blocked`; provider, runtime, browser, real-project and write actions remain prohibited.

## Next Safe Action

Record the evidence-provenance decision and implementation owner. Until then, keep P8 action-status read-only and do not enable proof submission or controlled runtime.
