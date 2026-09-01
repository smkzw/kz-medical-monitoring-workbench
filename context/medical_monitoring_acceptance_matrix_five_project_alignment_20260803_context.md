# Task Context: medical_monitoring_acceptance_matrix_five_project_alignment_20260803

Created: 2026-08-03
Objective: Align the future serial Playwright acceptance planning matrix with the five-project acceptance contract and current 40-row prompt manifest without dispatching testers or granting runtime authority.
Task type: `code_scoped_patch_plan`
Risk: `high`

## Source of truth

- `services/api/app/monitoring_real_loop_acceptance.py` frozen tester/role/project
  sets and Playwright-only evidence contract.
- `services/api/app/monitoring_real_loop_prompt_manifest.py` and its current
  v2 40-row artifact.
- `records/active_slices/medical_monitoring_real_loop_five_project_contract_reconciliation_20260803/`
  and current B6/C14/real-loop re-anchor.
- Historical `medical_monitoring_candidate_matrix_20260802/CANDIDATE_MATRIX.json`
  is retained as a superseded three-project planning snapshot.

## Scope

- In scope: create a new five-project candidate-matrix planning artifact,
  bind it to the v2 prompt manifest and exact tester/role/task policy, run a
  deterministic consistency check, and record the supersession boundary.
- Out of scope: tester/provider dispatch, browser/API login, service/runtime
  startup, real project files, source admission, B6/C14/CAS/source-token,
  SQLite/risk/disposition writes, or medical/UAT/release decisions.

## Done criteria

- New matrix declares exactly five acceptance projects, two roles, four tasks,
  five requested tester routes, Playwright-only login and two final clean rounds.
- Matrix references prompt manifest v2 with 40 rows and the current manifest
  digest; no old three-project digest remains in the new artifact.
- Current acceptance/readiness tests and a JSON consistency check pass; all
  authority/runtime/browser/provider flags remain false and listeners stay empty.

## Loop log

- 2026-08-03 22:16:26: Task initialized by workflow guard. The old candidate
  matrix was found to be a historical three-project/24-row snapshot while the
  executable acceptance contract is already five-project/40-row.
- 2026-08-03 22:19–22:22: Added the new v2 five-project planning matrix;
  prompt preflight passed after removing a production-like workspace path;
  deterministic matrix consistency passed; focused contract/readiness/prompt
  tests passed (53); review-gate passed. No tester/provider/browser/service
  was dispatched or started, and all four listeners remained empty.

## Workflow metadata

- Initialized by `tools/hermes_workflow_guard.py init-task` at 2026-08-03
  22:16:26; Codex direct route (`codex` / `codex-main` / `high`).
- This is a tracked offline reconciliation task. The task-scoped review gate
  passed, but upstream authority gates remain authoritative and closed.
