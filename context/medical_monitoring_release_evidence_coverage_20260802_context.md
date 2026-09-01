# Task Context: medical_monitoring_release_evidence_coverage_20260802

Created: 2026-08-02 10:58:35
Objective: Build a read-only current commercial release evidence coverage report for the medical-monitoring subsystem from the existing release audit and B6 payload; do not grant authority or modify runtime/product/medical-writing surfaces.
Task type: `code_open_audit`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `records/active_slices/medical_monitoring_goal_p10_20260730/RELEASE_GATE_AUDIT_20260802.md`
- `runs/execution/medical_monitoring_phase_b6_review_gate_20260801/B6_REVIEW_OUTCOME_GATE.json`
- `runs/execution/medical_monitoring_phase_c14_b6_activation_gate_20260802/B6_TO_C13_ACTIVATION_GATE_REPORT.json`
- `context/medical_monitoring_release_gate_contract_20260802.md`
- `services/api/app/monitoring_release_gate.py` and `tests/test_monitoring_release_gate.py`

All source inputs are read-only evidence. The report is a task-scoped evidence artifact, not a
runtime or authority surface.

## Scope

- In scope: bind the current release-audit rows to the canonical 16-gate evaluator, record source
  hashes, preserve the current B6/C13 fail-closed state, and produce a reproducible JSON coverage
  report.
- Out of scope: reviewer outcomes, aggregate/CAS replay, source-registry writes, migration,
  SQLite/API/provider/runtime activation, browser or real-project runs, and any medical-writing or
  shared frontend source change.

## Success Criteria

- The report contains one hash-bound evidence row for each required gate in canonical order.
- The pure evaluator returns `status=blocked` and `release_ready=false` from current B6 state.
- The report explicitly records that no authority or runtime write permission is granted.
- Focused release-gate tests and JSON/hash checks pass.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- 8911 and 5174 remain stopped; unrelated 18911/18913 processes are not touched.
- `frontend/src/App.jsx`, `frontend/src/styles.css`, backend runtime state, SQLite, providers, and
  the parallel medical-writing lane remain unchanged.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-02 10:58:35: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-02 10:59:38: Read-only source hashes captured; current release audit has 0 passed,
  12 partial, 3 unproven, and 1 blocked gate. B6 is `pending_review` with 5 candidates and 0 outcomes.
- 2026-08-02 11:00:00: Pure evaluator replayed from the current gate rows and B6 adapter; decision
  is `blocked/release_ready=false`, decision SHA is recorded in the evidence JSON.
