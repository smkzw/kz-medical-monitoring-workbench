# Task Context: medical_monitoring_project_set_traceability_20260802

Created: 2026-08-02 21:09:51
Objective: Reconcile historical P0 and current P10 medical-monitoring real-project sets without silently changing the commercial acceptance scope
Task type: `code_open_audit`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

The current P10 readiness contract and the older P0 matrix name different third-project candidates. This is a traceability risk for the eventual three-project commercial acceptance dossier and must be resolved from current local evidence before any real LOOP is run.

## Source Of Truth

- `records/active_slices/medical_monitoring_goal_p0_20260729/REAL_PROJECT_TEST_MATRIX.md` (historical P0 baseline).
- `records/active_slices/medical_monitoring_goal_p10_20260730/TASK_CONTEXT.md` (current P10 project table).
- `records/active_slices/medical_monitoring_goal_p10_20260730/REQUIREMENTS_TRACEABILITY.md` and `RELEASE_GATE_AUDIT_20260802.md` (current release traceability).
- `records/active_slices/medical_monitoring_real_loop_readiness_contract_20260802/REAL_LOOP_READINESS.json` and `services/api/app/monitoring_real_loop_readiness.py` (current executable scenario identity).
- `.hermes/plans/2026-08-01_210824-medical-monitoring-commercialization-goal.md` and the P10 `LOOP_LEDGER.md` (current Goal and decision history).

## Scope

- In scope: compare the historical P0 and current P10 project sets, classify MY008 evidence, and record the current canonical set without changing it.
- Out of scope: product source, source registry, runtime/SQLite, API, provider, browser, real-project execution, medical review, or any change to the commercial acceptance contract.

## Success Criteria

- Preserve the P0 `MY008211A-PNH-3-01` matrix as historical evidence.
- State explicitly that the current P10 canonical set is `proj_rux_03_002`, `proj_mgk10_sar_real`, and `proj_my009_uc` (RUX / MG-K10-SAR / MY009).
- Record that current MY008 3-02/2-03 evidence is an auxiliary candidate, not a silent replacement; its protocol-to-listing mapping remains blocked.
- Verify the wording against the current readiness JSON, P10 ledger, requirements traceability, and Goal plan.

## Risk Boundaries

- Only evidence/context/review/metrics/ledger surfaces in the workbench may be changed.
- Do not write to product source, source registry, runtime/SQLite, service state, provider state, browser state, or real project files.
- Do not infer reviewer approval, source eligibility, batch completeness, or commercial readiness from the project-set reconciliation.
- Codex remains final authority; no delegated route or external provider is used.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-02 21:09:51: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-02: Bounded evidence comparison found P0's PNH `3-01` as historical, while current P10 Goal/readiness repeatedly fix RUX + MG-K10-SAR + MY009. Current MY008 3-02/2-03 records are candidate/precheck evidence with mapping or adoption blockers.
