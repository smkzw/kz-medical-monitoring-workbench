# Task Context: medical_monitoring_real_loop_generalization_gate_20260804

Created: 2026-08-04 09:16:41
Objective: 将 anti-overfit generalization evidence 的完成标志与 SHA-256 绑定到五项目 RealLoopReadiness，缺失/非布尔/非法 hash 时 fail-closed，完成聚焦/相邻/全量验证
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Latest `AGENTS.md` files; `services/api/app/monitoring_real_loop_readiness.py`,
  `monitoring_ai_generalization.py`, `monitoring_ai_release_gate.py`, and
  their readiness/execution tests.
- LOOP 5.86 generalization evidence contract and current B6/C14 gate artifacts.

## Scope

- In scope: add strict `generalization_evidence_complete` and
  `generalization_evidence_sha256` prerequisites to `RealLoopGateInput`, carry
  the hash into the deterministic readiness report, and test missing,
  malformed and complete states.
- Out of scope: provider/runtime/queue/database/API, real projects, browser,
  B6/C14 changes, source/CAS writes, or acceptance execution.

## Success Criteria

- A readiness manifest with every other prerequisite true remains blocked when
  generalization evidence is absent, false, non-boolean or hash-invalid.
- A complete fixture with a lowercase SHA-256 profile snapshot is structurally
  ready only when all existing gates also pass; readiness still grants no
  runtime/provider/write authority.
- Existing deterministic readiness/execution behavior remains intact; focused,
  adjacent and full monitoring suites pass.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- The hash is a binding to the upstream generalization evidence record, not a
  substitute for the evidence itself; real five-project evidence remains
  blocked until the formal B6/source/CAS/approved-input sequence.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 09:16:41: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04 09:20:xx: Focused readiness/execution/acceptance/prompt-manifest tests initially
  exposed an invalid fixture placeholder (`g` is not hexadecimal); the fixture was corrected
  to `a`*64 and the invalid-input assertion was kept as a fail-closed diagnostic.
- 2026-08-04 09:21:xx: Focused suite passed 56/56; adjacent real-loop suite passed 66/66.
- 2026-08-04 09:29:21: Clean full `tests/test_monitoring*.py` passed 1959/1959 with 25
  existing warnings in 480.49s; reserved ports remained empty. Records/review/metrics were
  written.
- 2026-08-04 09:29:48: `review-gate --require-verification` returned
  `{"ok":true,"warnings":[],"errors":[]}`; LOOP 5.89 closed.
