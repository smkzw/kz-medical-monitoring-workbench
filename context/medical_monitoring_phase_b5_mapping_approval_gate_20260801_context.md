# Task Context: medical_monitoring_phase_b5_mapping_approval_gate_20260801

Created: 2026-08-01 23:31:34
Objective: Implement and verify an explicit approval gate for legacy-to-current risk mappings so only independently approved, hash-bound mappings can enter a non-writing dry-run; keep actual clone candidates unapproved.
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- B3 candidate mappings and B4 residual package under `runs/execution/medical_monitoring_phase_b3_mapping_dryrun_20260801/` and `runs/execution/medical_monitoring_phase_b4_residual_decision_20260801/`.
- `services/api/app/medical_risk_mapping.py` candidate model and in-memory remap.
- B1 `MedicalRiskEvent`/CAS contract and B2 reconciliation contract.

## Scope

- In scope: pure approval evidence model, candidate fingerprint binding, fail-closed approved-input dry-run, focused tests and review records.
- Out of scope: approving actual mappings, runtime writes, migration, dual-read promotion, service startup, frontend, real-project execution, or medical-writing changes.

## Success Criteria

- Approval evidence must name reviewer, timestamp, decision, candidate fingerprint, residual review status and source evidence.
- Reused or changed candidates, missing reviewer/decision, rejected decisions and unresolved residual blockers fail closed.
- A valid approved input may produce only an in-memory remapped record; no function writes or mutates the original record.
- Actual clone candidates remain unapproved and cannot pass this gate.

## Risk Boundaries

- Only source/test files inside this workbench plus task-scoped context/review/metrics records may change.
- No runtime DB, migration schema, service, router, frontend, medical-writing path, or frozen v9-v12 job may be changed.
- Approval evidence in tests is synthetic only; never fabricate approval for actual clone candidates.
- Codex is sole execution and acceptance authority; no Hermes/external route or sub-agent.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-01 23:31:34: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-01 23:32: B4 package confirms all five real candidates unapproved; this slice will implement the approval/fingerprint gate only.
- 2026-08-01 23:39: Added hash-bound `MedicalRiskMappingApproval` and fail-closed approved-input dry-run contract; synthetic approval tests pass, while actual clone candidates remain unapproved.
- 2026-08-01 23:39: Actual-candidate assertion confirms 5/5 `approved=false`, `write_permitted=false`, `review_required=true`, `gate_passed=false`; combined B1-B5/risk compatibility set 112 passed, 17 warnings.

## Closure And Next Safe Action

- B5 approval gate is complete; it deliberately leaves the real mapping gate closed.
- Next safe action requires an explicit external/medical review outcome for each actual candidate and residual blocker; only then can an approved-input dry-run be run. No runtime migration, dual-read promotion, or service start is authorized by this checkpoint.
