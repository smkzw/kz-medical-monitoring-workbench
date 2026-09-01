# Task Context: medical_monitoring_assurance_remediation_preview_20260803

Created: 2026-08-03 21:09:37
Objective: Expose a strict read-only pre-inspection remediation matrix preview for site and subject self-check without changing assurance gates or dispositions
Task type: `finite_code_task`
Risk: `medium`
Selected agent route: `opencode-go` / `deepseek-v4-flash` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Assurance consumer: `frontend/src/features/medical-monitoring/MedicalMonitoringAssurancePanel.jsx` and `.css`.
- Existing contract/model: `medicalMonitoringAssuranceView.mjs`, `medicalMonitoringAssuranceRollup.mjs`, `medicalMonitoringAssurance.mjs`.
- Backend reference shape: `services/api/app/monitoring_assurance_service.py` remediation matrix entries contain risk_instance_id, risk_key, subject_id, site_id, severity, status and closure_evidence_present; the frontend API normalizer already requires the matrix to be an array.
- Current filesystem is authoritative. This is a read-only pre-inspection presentation consumer; no task completion or disposition writes are allowed.
- Release boundary: B6/C14, source-token/CAS and real-loop evidence remain fail-closed; no service, browser, provider or real project may be started.

## Scope

- In scope: strict remediation-matrix normalizer/sorter, compact top-priority checklist preview in the existing pre-inspection assurance rollup, focused/full frontend tests/build and task evidence.
- Out of scope: backend/API changes, assurance task state, remediation/disposition writes, rollup/conservation logic changes, release gates, browser/Playwright, real projects, or clinical interpretation.

## Success Criteria

- Explicit matrix entries are shown with subject/site, severity, status and closure-evidence state; malformed entries remain visible as an evidence warning and are excluded from priority rows.
- Priority ordering is deterministic and documented (open/high first, then missing closure evidence, then stable risk ID); the preview never claims the omitted rows are resolved.
- Existing conservation and completion banners remain unchanged; no action button writes or bypasses a gate.
- Focused model, all medical-monitoring Node tests, Vite build and empty-port check pass; durable records are complete.

## Risk Boundaries

- Only the workbench frontend assurance feature, derived build output and task evidence files may change.
- Do not infer clinical urgency from severity strings beyond the explicit display ordering; do not infer closure from omission or empty arrays.
- No disposition, task transition, risk state, API, runtime, B6/C14 or source evidence mutation. Codex remains final authority.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-03 21:09:37: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-03: Direct Codex slice planned after inspecting the backend remediation-matrix shape and current pre-inspection UI; external execution intentionally not dispatched.
- 2026-08-03: Added strict remediation-matrix preview and focus callbacks inside the pre-inspection rollup. Focused model, all 28 medical-monitoring Node files and Vite build passed; no task state, disposition, runtime or release-gate action occurred.
