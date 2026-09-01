# Task Context: medical_monitoring_project_source_adapter_reconciliation_20260802

Created: 2026-08-02 23:53:53
Objective: 建立五个候选医学监查项目的来源、适配器、批次、提示词与安全准入的只读对账契约，不改变 canonical project set，不启动运行时，不修改产品源码
Task type: `high_risk_contradiction_review`
Risk: `high`
Selected agent route: `codex` / `gpt-5.6-luna` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `records/active_slices/medical_monitoring_candidate_matrix_20260802/CANDIDATE_MATRIX.json`
- `records/active_slices/medical_monitoring_real_loop_acceptance_contract_20260802/ACCEPTANCE_CONTRACT.json`
- `records/active_slices/medical_monitoring_real_loop_readiness_contract_20260802/REAL_LOOP_READINESS.json`
- `runs/execution/medical_monitoring_phase_b6_review_gate_20260801/B6_REVIEW_OUTCOME_GATE.json`
- `runs/execution/medical_monitoring_phase_c14_b6_activation_gate_20260802/B6_TO_C13_ACTIVATION_GATE_REPORT.json`
- Static source inspection of `services/api/app/main.py`, `monitoring_project_registry.py`, `project_source_manifest.py`, and the real-loop readiness/prompt modules.
- User-authorized candidate roots are recorded in the candidate matrix; root existence and exact canonical source paths were checked read-only.

## Scope

- In scope: reconcile the five requested candidate roots with the current monitoring adapter registrations, raw-source configurations, source-manifest builders/module bindings, frozen prompt rows, batch/readiness evidence, and B6/C14 gates; record exact evidence and the next safe admission sequence.
- Out of scope: changing the canonical project set, adding adapters, registering sources, modifying runtime/SQLite/CAS, calling providers, launching services, browser login, real-project execution, medical dispositions, or changing the medical-writing subsystem.

## Success Criteria

- A validated JSON reconciliation artifact distinguishes canonical-but-blocked projects from candidate-only roots and separates medical-writing/TFL identities from monitoring identities.
- Every project row states whether adapter, raw config, source-manifest monitoring binding, batch evidence, and prompt rows are present; absence is fail-closed rather than inferred from a directory listing.
- The artifact records the current B6/C14/readiness state and a bounded next action without granting execution authority.
- Product source, runtime, listeners, canonical project IDs, and prompt manifest remain unchanged.

## Risk Boundaries

- Only the task-scoped evidence/context/review/metrics surfaces under this workspace may be written.
- Do not write to product source, runtime/SQLite/CAS, user project roots, provider configuration, or browser state.
- A directory existing, a source path existing, or a non-monitoring project manifest entry is not evidence of monitoring admission.
- B6 engineering defer records are not medical approvals; no reviewer outcome may be invented.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-02 23:53:53: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-02 23:54:20: Re-read current candidate matrix, acceptance/readiness contracts, B6/C14 gate, and static adapter/source-manifest registrations.
- 2026-08-02 23:54:55: Created `records/active_slices/medical_monitoring_project_source_adapter_reconciliation_20260802/PROJECT_SOURCE_ADAPTER_RECONCILIATION.json`; product/runtime/provider/browser boundaries remained unchanged.
