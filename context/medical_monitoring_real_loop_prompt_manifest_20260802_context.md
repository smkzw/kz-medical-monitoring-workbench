# Task Context: medical_monitoring_real_loop_prompt_manifest_20260802

Created: 2026-08-02 22:21:35
Objective: 建立三项目医学监查真实 LOOP 的可审计 prompt manifest，并将 readiness/execution 场景身份绑定到 prompt reference 与正文 hash；不启动服务/provider/browser，不升级任何真实 gate
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_real_loop_readiness.py` and its canonical
  project/role/task constants.
- `services/api/app/monitoring_real_loop_execution.py` and its exact scenario
  evidence identity.
- `records/active_slices/medical_monitoring_real_loop_readiness_contract_20260802/REAL_LOOP_READINESS.json`.
- Current product and global `AGENTS.md`; 8911/5174 remain stopped.

## Scope

- In scope: a pure offline prompt manifest builder/validator; `prompt_ref`
  binding in readiness and execution contracts; focused tests and an audit
  metadata artifact.
- Out of scope: provider dispatch, runtime/API/SQLite/browser startup, real
  project source registration, B6/C14/source-token/CAS changes, medical
  decisions, frontend changes and release approval.

## Success Criteria

- Exactly 24 deterministic rows cover all three projects, both roles and all
  four required tasks.
- Every row contains exact prompt text, stable identity, a distinct reference,
  and the exact UTF-8 SHA-256 of that text.
- Readiness fails closed if the manifest is absent or a scenario reference/hash
  does not match; execution evidence binds the same reference.
- Focused tests, compile and Ruff checks pass, and the frozen audit metadata
  matches the source builder.

## Risk Boundaries

- Only the prompt contract, its tests, task records and audit metadata may be
  written in this slice.
- The contract never grants provider, runtime, migration, database or medical
  authority and does not upgrade the blocked real-loop readiness report.
- Do not touch the protected frontend, real project source files, shared
  runtime/SQLite, 8911, 5174 or the medical-writing subsystem.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-02 22:21:35: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-02: Identified the hash-only prompt gap after re-reading readiness and
  execution contracts. Selected a small pure module plus explicit scenario
  binding rather than adding provider/runtime behavior.
- 2026-08-02: Implemented the 24-row manifest, readiness/execution binding and
  frozen metadata; focused contract test set passed 26/26.
