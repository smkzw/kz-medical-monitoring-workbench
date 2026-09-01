# Task Context: medical_monitoring_p8_proof_transport_provenance_20260806

Created: 2026-08-06 03:50:13
Objective: Expose current mixed-provenance P8 proof status in the server transport without selecting or implementing an evidence authority route
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `docs/medical_monitoring_manual/医学监查子系统说明书.md` §§11.2, 40.5
- `docs/medical_monitoring_manual/医学监查子系统_PRD审阅与差距矩阵.md`
- `context/p8_assurance_proof_provenance_audit_20260806_context.md`
- `records/active_slices/medical_monitoring_p8_evidence_provenance_ui_guard_20260806/DECISION_REQUIRED.md`
- `services/api/app/monitoring_assurance_router.py`
- `services/api/app/monitoring_assurance_repository.py`
- `frontend/src/features/medical-monitoring/medicalMonitoringAssuranceView.mjs`
- `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json`
- Current P10 `LOOP_LEDGER.md`, `REQUIREMENTS_TRACEABILITY.md` and roadmap tail.

The filesystem gate is authoritative: `read_only / blocked`; all activation,
provider, runtime and write flags are false and ports 8911/5174/8910/4173 must
remain stopped.

## Scope

- In scope: add a server transport annotation to the existing P8 full-recompute
  proof responses that explicitly reports the currently observed mixed
  provenance; add focused regression coverage and durable evidence records.
- Out of scope: choosing server evidence-run ledger versus signed-manifest
  authority, changing proof persistence/content hashes, accepting caller
  provenance claims, enabling submit/complete actions, changing B6/C14,
  runtime/provider/browser/real-project work, or changing medical-writing.

## Success Criteria

- Both POST and GET full-recompute proof responses expose
  `provenance_status: mixed_provenance` while the current backend still accepts
  mixed caller/risk-reader fields.
- The annotation does not alter the persisted proof payload or its content hash.
- Assurance/repository/principal tests, medical-monitoring Node tests, syntax
  checks and Vite build pass.
- The P8 consumer remains fail-closed and the formal real-loop gate remains
  blocked/read-only.

## Risk Boundaries

- No service, database, provider, browser, API login, real-project, source-token,
  aggregate/CAS, B6/C14 or medical-writing action.
- Do not infer that the transport annotation is an authority approval or a
  release decision; it is a diagnostic of the current mixed implementation.
- Preserve existing proof persistence and legacy read compatibility.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-06 03:50:13: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-06: Re-anchored latest AGENTS hashes, P10 checkpoint and real-loop gate;
  all unchanged and runtime ports empty.
- 2026-08-06: Confirmed canonical batch-diff and snapshot-proof slices are already
  present in P10 Ledger/traceability/roadmap; no duplicate documentation change.
- 2026-08-06: Implemented `_public_full_recompute_proof` transport annotation in
  `monitoring_assurance_router.py`; no repository/schema/content-hash change.
- 2026-08-06: Added POST/GET response assertions and ran focused/full assurance,
  Node, syntax and Vite verification.
