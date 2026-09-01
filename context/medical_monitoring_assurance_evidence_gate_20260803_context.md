# Task Context: medical_monitoring_assurance_evidence_gate_20260803

Created: 2026-08-03 05:19:18
Objective: 收紧核查前保障 rollup 完成门，使三级风险身份守恒和关闭依据缺失可见且不被误报为 ready
Task type: `code_scoped_patch_plan`
Risk: `medium`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `docs/medical_monitoring_manual/医学监查子系统_分阶段实施与LOOP计划.md` §12 P8 (lines 338-360):
  the pre-inspection exit gate requires three-level numbers to agree and every closed/
  explained item to have verifiable evidence.
- `frontend/src/features/medical-monitoring/medicalMonitoringAssurance.mjs`:
  current `assuranceEvidenceState` implementation.
- `frontend/src/features/medical-monitoring/medicalMonitoringAssuranceRollup.mjs`:
  current typed rollup projection and conservation calculation.
- `frontend/src/features/medical-monitoring/MedicalMonitoringAssurancePanel.jsx`:
  current user-facing evidence banner and three-level drill-down.
- Existing focused tests:
  `frontend/src/features/medical-monitoring/medicalMonitoringAssurance.test.mjs` and
  `medicalMonitoringAssuranceRollup.test.mjs`.
- Existing backend assurance contract:
  `services/api/app/monitoring_assurance_service.py`,
  `services/api/app/monitoring_assurance_repository.py`, and
  `tests/test_monitoring_assurance.py`.

## Scope

- In scope: make the pre-inspection evidence readiness helper require a valid typed
  rollup, exact trial/site/subject `risk_instance_id` conservation, and zero explicit
  `closed_risks_lacking_evidence_count`; expose a concise blocked reason to the existing
  evidence banner; add focused and static contract tests.
- Out of scope: backend routes/repository/service, risk facts, B6/C14 outcomes, runtime
  databases, API POST actions, real projects, browser/server/provider execution, App.jsx,
  protected medical-writing surfaces, and any claim of P8 or release completion.

## Success Criteria

- A valid pre-inspection rollup with conserved IDs and zero missing closure evidence is
  `ready=true`.
- A malformed, non-conserved, missing-count, or closure-evidence-incomplete rollup is
  `ready=false` and reports a user-readable blocking reason; no malformed object is
  promoted by truthiness.
- Existing pre-lock proof behavior remains unchanged.
- Focused tests, all medical-monitoring Node contract tests, relevant Python frontend
  contract tests, and offline production build pass without starting a service.
- The change remains read-only with respect to authority and runtime state; B6/C14 and
  8911/5174 stay unchanged/stopped.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-03 05:19:18: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-03 05:21: source and P8 exit-gate contract reanchored; no external discovery was
  needed because this is a local fail-closed contract correction using existing canonical
  rollup logic.
- 2026-08-03: `medicalMonitoringAssurance.mjs` now requires a valid projected rollup,
  three-level risk-identity/count conservation, and zero explicit closed-risk-without-
  evidence count before pre-inspection evidence is `ready`; pre-lock evidence now uses
  the same fail-closed label/tone distinction for recorded-but-blocked proof.
- 2026-08-03: the evidence banner shows the typed blocking reason; focused assurance
  tests report 23 passed, all 22 medical-monitoring Node files pass, Python assurance/
  frontend contract tests report 48 passed, Ruff passes, and Vite production build
  succeeds (1926 modules; existing large-chunk warning only).
- 2026-08-03: final boundary recheck confirms App.jsx/style protected hashes unchanged;
  B6 remains `pending_review` with 5 candidates/5 engineering outcomes/0 accepted
  reviewer ids, C14 remains `blocked_pending_b6_review`, and 8911/5174 have no listeners.
