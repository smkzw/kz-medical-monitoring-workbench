# Task Context: medical_monitoring_ai_deterministic_repair_root_read_shape_revalidation_20260805

Created: 2026-08-05 05:30:46
Objective: Fail closed on malformed persisted monitoring AI deterministic-repair root rows
Task type: `finite_code_task`
Risk: `high`
Selected agent route: `alibaba` / `qwen3.8-max` / `xhigh`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_ai_repository.py`
  (`_deterministic_repair`, repair schema/read/write paths).
- `tests/test_monitoring_ai_v7_deterministic_repair.py` plus monitoring AI
  repository, module-contract and risk-bridge suites.
- Current filesystem state and
  `records/active_slices/medical_monitoring_goal_p10_20260730/LOOP_LEDGER.md`.
- Real-loop and release gates remain authoritative and blocked; this slice is
  source-only and cannot activate runtime or external providers.

## Scope

- In scope: validate persisted repair identifiers, hashes, original status/
  failure metadata, attempt count, actor/reason and timestamp; preserve raw
  output legacy compatibility and provenance/hash checks; add focused tamper
  regressions, run AI adjacency, compile/Ruff, hashes, evidence and review
  gate.
- Out of scope: services, ports, browsers/Playwright, real project data,
  external providers, medical judgments, new repair hash/schema schemes,
  runtime/release activation and provider execution.

## Success Criteria

- Valid deterministic repairs round-trip unchanged after restart.
- A malformed repair root field or invalid SHA/timestamp fails closed before a
  caller receives the repair.
- Focused/adjacent tests, compileall, Ruff and reserved-port checks pass; the
  evidence records exact counts, hashes, warnings and residual limits.
- Review gate reports `ok: true` with no warnings/errors.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 05:30:46: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05: Codex direct source-only implementation selected; no Hermes
  execution session, provider call or sub-agent dispatch.
- 2026-08-05: Hardened deterministic-repair root fields and added five
  isolated tamper regressions, including uppercase SHA rejection. Focused 87
  and adjacent 832 passed (17 pre-existing warnings); compileall/Ruff passed;
  ports remained free.
- **Residual/next**: repair read integrity does not prove provider quality,
  clinical correctness, browser usability, formal B6 review, C14 activation or
  commercial release. Continue with a bounded structural P7/P8/P9 source-only
  gap; keep runtime gates closed.
