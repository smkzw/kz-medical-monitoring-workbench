# Task Context: medical_monitoring_release_dossier_contract_20260802

Created: 2026-08-02 21:38:34
Objective: Add a pure offline fail-closed commercial release dossier contract and adapter for the medical-monitoring release gate, covering nonfunctional, install/upgrade/rollback, security/privacy, audit, operator/UAT, and residual-risk evidence without granting authority.
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `docs/medical_monitoring_manual/医学监查子系统说明书.md` sections 29–31 and Appendix D: deployment, performance, audit, testing, release and continuous-improvement requirements.
- `context/medical_monitoring_release_gate_contract_20260802.md` and `services/api/app/monitoring_release_gate.py`: current 16-gate pure evaluator and its no-authority boundary.
- `records/active_slices/medical_monitoring_goal_p10_20260730/RELEASE_GATE_AUDIT_20260802.md` and `records/active_slices/medical_monitoring_release_evidence_coverage_20260802/CURRENT_RELEASE_COVERAGE.json`: current filesystem release state (`blocked`, no passed gates).
- `services/api/app/monitoring_migration_contract.py`, `monitoring_ai_release.py`, and `monitoring_ai_release_gate.py`: adjacent immutable migration and independent-AI release contracts.
- Product `AGENTS.md` and workspace/global AGENTS: surgical edits, fail-closed evidence, no runtime/provider/SQLite/port writes in this slice, and Codex final acceptance.

## Scope

- In scope: add one pure in-memory `monitoring_release_dossier.py` contract; require canonical dossier sections and control coverage for functional, non-functional, install/upgrade/rollback, security/privacy/SBOM, audit/retention, operations/training, UAT, and residual-risk release evidence; add a strict adapter that binds the dossier hash/status to the existing `commercial_release_dossier` gate; add focused tests and task evidence.
- Out of scope: B6 reviewer outcomes, source-token revalidation, aggregate/CAS replay, runtime/API/SQLite/provider activation, real projects, browser sessions, 8911/5174, frontend source, medical-writing code, generated release coverage JSON, or claiming any commercial release readiness.

## Success Criteria

- Missing, duplicated, unknown, stale, malformed, or incomplete dossier evidence fails closed.
- A synthetic complete dossier can produce a hash-bound `commercial_release_dossier` gate evidence row, while authority flags remain false and the real filesystem dossier remains blocked.
- The adapter rejects a stale/mismatched pre-existing commercial gate instead of silently replacing it.
- Focused tests, compile, Ruff, and adjacent release/migration/AI regressions pass; no service/provider/browser/SQLite/port is started or modified.

## Risk Boundaries

- Only the new module, its focused test, this task's context/review/metrics/active-slice evidence, and the P10/Goal/roadmap checkpoint may be written.
- The contract is diagnostic and immutable: it cannot grant medical, runtime, migration, provider, or database-write authority.
- No current release evidence is upgraded by synthetic fixtures; real `CURRENT_RELEASE_COVERAGE.json` remains `blocked` until independently refreshed from evidence.
- Do not modify `frontend/src/App.jsx`, `frontend/src/styles.css`, runtime stores, source registries, real project files, ports, or the medical-writing subsystem.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-02 21:38:34: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-02: Existing release/migration/AI contracts reviewed. Decision: a separate dossier contract is the smallest non-redundant change because the generic release gate currently accepts one arbitrary `commercial_release_dossier` summary and no contract binds its required commercial controls.
