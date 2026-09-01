# Task Context: medical_monitoring_phase_b7_shared_risk_projection_20260801

Created: 2026-08-01 23:53:29
Objective: Define and test a read-only shared medical-risk projection for project/site/subject drilldown, Timeline/Profile/AE linkage and progressive disclosure without introducing a second fact source or requiring runtime migration
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/medical_risk_authority.py` (`MedicalRiskAggregate.public_dict()`)
- `frontend/src/features/medical-monitoring/medicalMonitoringModels.mjs`
- `frontend/src/features/medical-monitoring/medicalMonitoringSubjectModels.mjs`
- `frontend/src/features/medical-monitoring/MedicalMonitoringSubjectViews.jsx`
- `frontend/src/features/medical-monitoring/MedicalMonitoringRiskChecklist.jsx`
- `reviews/medical_monitoring_system_retro_roadmap_20260801.md` §7.4 and Phase B-I
  product contracts; local skills already synthesized in that roadmap.
- Current filesystem is authoritative; no runtime database, service or browser session
  is an allowed write target for this slice.

## Scope

- In scope: a pure frontend projection that consumes canonical aggregate-shaped risk
  rows, preserves finding class/severity/status/unread/disposition/source evidence as
  separate fields, and derives deterministic project→site→subject drilldown counts.
- In scope: explicit linkage fields for Timeline/Profile/AE/lab/vital/ECG/PD evidence,
  progressive-disclosure metadata, and tests for duplicate identity/count conservation.
- Out of scope: replacing the existing API, wiring runtime dual-read, changing root
  `App.jsx`, creating a second database/source, UI styling overhaul, service start,
  browser execution, historical mapping approval or any runtime write.

## Success Criteria

1. The projection accepts only an explicit `risk_instance_id` and project/trial/scope
   identity; missing identity is rejected instead of guessed from title/text.
2. Risk fact (`findingClass`, category, severity, detection status), workflow
   (`unread`, disposition, query state) and evidence (`sourceRevision`, rule,
   locators, linked event IDs) stay separate and remain round-trippable.
3. Project/site/subject summaries use distinct risk-instance IDs and deterministic
   ordering; totals conserve across drilldown and do not double-count a risk.
4. Timeline/Profile/AE/lab/vitals/ECG/PD links are explicit arrays/IDs; no view can
   infer clinical linkage from display text.
5. Empty/uncertain/limited inputs degrade visibly and never become a false success.
6. Node-focused tests pass; no backend/runtime state changes occur.

## Risk Boundaries

- Codex direct only; no external agent, conference, service, browser or real project.
- This is a read-only projection contract; it must not silently become a second fact
  source or infer missing clinical meaning.
- Preserve existing frontend behavior by adding an isolated module/test only; do not
  reformat or refactor `App.jsx` or existing model functions in this slice.
- Codex owns final review and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-01 23:53:29: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-01 23:54: direct task contract filled; implementation will remain an isolated
  pure projection until Phase B authority migration and UI integration are authorized.
- 2026-08-01 23:59: added the pure canonical-risk projection and 16 focused checks. The
  complete medical-monitoring frontend Node feature sweep passed; no runtime/UI wiring
  was attempted. B6 mapping review remains the authority blocker for future integration.
- 2026-08-02 00:05: final metadata/hash checkpoint updated after the projection's explicit
  empty/limited-input checks; the same non-writing boundary remains in force.
