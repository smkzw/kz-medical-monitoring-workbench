# Task Context: medical_monitoring_real_loop_upstream_assembly_20260804

Created: 2026-08-04 10:21:42
Objective: 为五项真实 LOOP upstream evidence 建立来源感知的只读装配合同，禁止手工布尔值绕过 artifact 状态与 ref/hash 绑定
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Latest global/workspace/workbench `AGENTS.md` and current filesystem.
- `services/api/app/monitoring_real_loop_readiness.py`, its tests, and LOOP 5.91/5.92 upstream
  binding records/reviews.
- Existing B6/C14, approved-input, source-token and aggregate-CAS artifact identities are evidence
  data only; no current outcome may be inferred. Current truth is B6 `pending_review`, C14
  `blocked_pending_b6_review`, approved input blocked, source-token `not_proven`, aggregate/CAS
  incomplete, and runtime identity not yet verified.

## Scope

- In scope: define a source-aware, read-only assembly boundary that accepts five explicit evidence
  rows, derives strict gate booleans only from an explicit `proven` status, preserves unresolved
  evidence as false, and maps each row to one opaque ref/hash pair for `RealLoopGateInput`.
- Out of scope: changing actual gate JSON, reviewer decisions, API/runtime/provider/queue/database,
  browser/Playwright, real projects, B6/C14 activation or medical conclusions; no path is treated
  as an opaque ref and no current artifact is promoted.

## Success Criteria

- Only an explicit, valid `proven` row can produce a true upstream prerequisite; `fresh`, `blocked`,
  `not_proven`, `missing` or unknown status never become true by coercion.
- Five rows must cover each canonical gate exactly once; valid refs/hashes are distinct and map
  deterministically into `RealLoopGateInput`, while malformed rows fail closed with diagnostics.
- Focused/adjacent/full monitoring tests pass, reserved ports stay empty and review-gate is clean.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- This is direct Codex work; no delegated agent/provider is dispatched.
- Refs are opaque evidence identities, not permission to read or promote an artifact. A row's
  `proven` status is caller-attested input to this pure boundary and must be backed by separate
  artifact/revalidation checks before any real gate is reopened.
- Keep B6/C14 and 8911/5174/8910/4173 closed; no real project or browser/runtime execution.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 10:21:42: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04 10:22:00: Static audit found `RealLoopGateInput` still accepted manually asserted
  booleans/hashes; no single source-aware assembler prevented `fresh` or `blocked` evidence from
  being misrepresented as a proven prerequisite.
- 2026-08-04: Added `monitoring_real_loop_upstream_assembly.py`. It requires the five canonical
  gates and expected evidence kinds, maps only explicit `proven` rows to true, preserves valid
  unresolved ref/hash pairs for audit continuity, and fails closed on malformed/duplicate/half
  pairs. It never reads or writes files and never grants authority.
- 2026-08-04: Focused assembly/readiness/execution 44 passed; adjacent real-loop 87 passed; full
  `tests/test_monitoring*.py` 1980 passed with 25 existing warnings (494.06s, rc 0). The current
  filesystem gate-artifact read-only test kept all five booleans false. Final ports 8911/5174/
  8910/4173 were empty; records/review/metrics are ready for review-gate.
