# Task Context: safety_pv_shared_contract_design_20260713

Created: 2026-07-13 07:26:14
Objective: 在不预设旧Safety/PV界面去留的前提下，设计医学监查复用视图与PV文件医学审阅的共享契约、迁移依赖和RUX/MY009双项目验收矩阵
Task type: `code_open_audit`
Risk: `high`
Selected agent route: `reasonix-cli` / `deepseek-v4-pro` / `xhigh`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- User-approved product definition recorded in `records/active_slices/safety_pv_redesign_20260713/DISCOVERY_RECORD.md`.
- Current shared contracts: `packages/contracts/workbench_contracts/models.py`.
- Monitoring ownership and project adapters: `services/api/app/monitoring_project_registry.py`, `services/api/app/rux_monitoring_service.py`, `services/api/app/my009_monitoring_service.py`.
- Medical-writing document and collaboration kernel: `services/api/app/medical_writing_document.py`, `services/api/app/medical_writing_repository.py`, `services/api/app/medical_writing.py`.
- Legacy Safety/PV implementation to be migrated: `services/api/app/safety_pv_manifest.py`, `services/api/app/safety_pv_review_workbench.py`.
- Current route surface: `services/api/app/main.py`.
- Existing real-project regression suites listed under `tests/` and `frontend/tests/`.
- Real project source files remain read-only in their original locations; the user has explicitly authorized read access.

## Scope

- In scope: ownership boundaries, compatibility-first contract changes, API projection design, migration dependencies, RUX-03-002/MY009 acceptance matrix, source-version/CAS/audit invariants, and a record of unresolved user decisions.
- Out of scope: choosing A/B/C on the user's behalf, changing production code before the Product Design Brief Gate, final PV judgment/reporting, building a duplicate PV case-processing or signal-management system, and security scanning of trusted internal/authority files.

## Success Criteria

- Every longitudinal safety item shown through Safety/PV resolves to the same monitoring event, trend point, risk ID, source revision and disposition state.
- PV document review reuses one writing-document working copy, revision-thread, evidence, CAS and approval implementation rather than introducing a second editor or audit store.
- DSUR, SAE report, CTD 2.7.4 and ISS keep distinct requirement profiles and do not collapse into one template.
- Content validation checks project/indication/document role/version and supports warned expert override; it does not introduce heavy security scanning.
- RUX-03-002 and MY009 each have end-to-end test cases for every visible control and critical backend state transition, including source replacement and stale-write rejection.
- Migration keeps existing protocol-writing behavior compatible until all callers are moved.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- Keep CM limited to non-investigational concomitant medication; investigational product interruption, dose adjustment and other study-drug changes remain separate events/lanes.
- Do not copy monitoring risks, Timeline/Profile data or document contents into a second Safety/PV fact store.
- AI output remains a traceable medical-review candidate requiring medical approval; no AI output becomes a formal PV conclusion or regulatory submission action.
- Keep the old Safety/PV public interface unchanged until the user selects A, B or C and approves the Product Design Brief.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-13 07:26:14: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-13: Codex inspected current contracts, services, routes and regression inventory. The generated Reasonix route will not be dispatched for a material product decision; the approved Hermes conference route will be used after the user resolves the A/B/C migration boundary.
