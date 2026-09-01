# Task Context: medical_monitoring_real_loop_upstream_evidence_binding_20260804

Created: 2026-08-04 09:50:31
Objective: 将 B6/approved-input/source-token/aggregate-CAS/runtime identity readiness flags 绑定到显式上游 evidence SHA-256，缺失或复用时 fail-closed；仅做离线验证
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- 最新 global/workspace/workbench `AGENTS.md` 与当前文件系统。
- `services/api/app/monitoring_real_loop_readiness.py` 及其 readiness/execution tests。
- `records/active_slices/medical_monitoring_real_loop_readiness_contract_20260802/`,
  `medical_monitoring_approved_input_source_binding_20260803/`, aggregate-CAS/source-token
  revalidation records and B6/C14 gate reports.
- LOOP 5.90 evidence-chain continuity record; readiness report hash is already upstream of
  execution/acceptance evidence but the five prerequisite booleans remain manually supplied.

## Scope

- In scope: add explicit SHA-256 fields for B6, approved-input, source-token,
  aggregate-CAS and runtime-identity evidence to `RealLoopGateInput`; require a valid,
  non-reused hash whenever the corresponding prerequisite is true; carry valid hashes into
  the deterministic readiness report and its payload; add fail-closed tests/records.
- Out of scope: changing gate outcomes, reviewer dispositions, source files, package JSON,
  API/runtime/provider/queue/database/browser/Playwright, real projects, B6/C14 activation,
  or any medical/commercial conclusion.

## Success Criteria

- A readiness fixture cannot become execution-ready by setting a prerequisite boolean true
  without a valid, distinct upstream evidence SHA-256.
- Missing/malformed/duplicated evidence hashes produce explicit issues and never grant
  provider/runtime/write authority; valid hashes are deterministic in the report hash.
- Existing blocked legacy and false-gate positional calls remain structurally compatible;
  focused and adjacent suites pass, reserved ports stay empty, review-gate is clean.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- This binds evidence identity only; it does not validate the content or create/infer any
  B6 medical outcome, source-token proof, CAS completion or runtime identity.
- Keep B6/C14 and 8911/5174/8910/4173 closed; no external agent/provider is dispatched.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 09:50:31: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04 09:51:00: Static audit confirmed `RealLoopGateInput` accepted five prerequisite
  booleans without any identity binding to existing B6, approved-input, source-token,
  aggregate-CAS or runtime-identity evidence artifacts.
- 2026-08-04 09:53:30: Focused readiness/execution tests passed 30/30; adjacent real-loop
  suite passed 73/73. Added five distinct upstream hash fields, duplicate protection and
  execution-ready direct-report invariants.
- 2026-08-04 10:01:51: Clean full `tests/test_monitoring*.py` passed 1966/1966 with 25
  existing warnings in 487.41s; reserved ports remained empty. Records/review/metrics were
  written.
- 2026-08-04 10:02:08: `review-gate --require-verification` returned
  `{"ok":true,"warnings":[],"errors":[]}`; LOOP 5.91 closed.
