# Task Context: medical_monitoring_p8_provenance_disclosure_20260806

Created: 2026-08-06 03:58:09
Objective: Add a collapsed senior-monitor disclosure explaining why current mixed-provenance P8 proof is not completion evidence
Task type: `code_scoped_patch_plan`
Risk: `medium`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `docs/medical_monitoring_manual/医学监查子系统说明书.md` §§11.2, 40.5
- `context/p8_assurance_proof_provenance_audit_20260806_context.md`
- `records/active_slices/medical_monitoring_p8_evidence_provenance_ui_guard_20260806/DECISION_REQUIRED.md`
- `records/active_slices/medical_monitoring_p8_proof_transport_provenance_20260806/VERIFICATION.md`
- `frontend/src/features/medical-monitoring/MedicalMonitoringAssurancePanel.jsx`
- `frontend/src/features/medical-monitoring/MedicalMonitoringAssurancePanel.css`
- `frontend/src/features/medical-monitoring/medicalMonitoringAssurance.mjs`
- `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json`

The current gate is `read_only / blocked`; no activation, provider, runtime or
write authority is available.

## Scope

- In scope: a collapsed, read-only, project/task-scoped disclosure in the P8
  assurance panel that explains the current `mixed_provenance` blocker in
  concise Chinese for a senior medical monitor; associated CSS, static
  contract assertions and regression evidence.
- Out of scope: evidence-authority selection or implementation, API/database
  changes, proof writes, runtime/provider/browser/real-project work, medical
  writing, or a second source of risk facts.

## Success Criteria

- Default panel density remains compact; technical detail appears only after
  the user opens the disclosure.
- The disclosure is shown only for a pre-lock proof explicitly marked
  `mixed_provenance` and states that it is not completion evidence.
- It describes the mixed origin without assigning unverified field-level
  authority, distinguishes read-only diagnosis from completion evidence and
  points to the pending authority decision.
- Existing Node/Python contracts and Vite build remain green; no runtime gate
  is changed.

## Risk Boundaries

- Read-only UI copy only; do not add submit controls or infer approval.
- Preserve medical-writing and shared shell files; edit only the monitoring
  assurance panel, its scoped CSS/test and task records.
- Do not start services, ports, providers, browsers, API login or real projects.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-06 03:58:09: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-06: Rechecked latest AGENTS hashes, P10 checkpoint and blocked gate;
  all unchanged.
- 2026-08-06: Added the disclosure and a provenance-only state path. Mixed
  proof responses remain rejected by `normalizeAssuranceProofPayload`; the
  task identity stays available for explanation, while no proof counts enter
  the completion policy.
- 2026-08-06: Focused Python contracts passed (43), adjacent assurance/module
  contracts passed (187 total), all 37 medical-monitoring Node test files
  passed, and the Vite build passed. Reserved ports remain unused.
