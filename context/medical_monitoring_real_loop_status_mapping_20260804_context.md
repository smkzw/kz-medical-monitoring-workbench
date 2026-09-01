# Task Context: medical_monitoring_real_loop_status_mapping_20260804

Created: 2026-08-04 10:38:44
Objective: 为现有五项 real-loop upstream revalidation payload 建立保守状态推导，拒绝形状漂移或未定义 runtime schema 的隐式放行
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Latest global/workspace/workbench `AGENTS.md` and current filesystem.
- `monitoring_real_loop_upstream_assembly.py`, `monitoring_real_loop_readiness.py`, and the
  source-specific revalidation modules/tests for B6, approved-input, source-token and aggregate/CAS.
- Current persisted JSON observations: B6 `pending_review`, approved input blocked, source-token
  `not_proven`, aggregate/CAS replay incomplete; no formal runtime-identity evidence schema exists.

## Scope

- In scope: add a conservative, source-specific status derivation helper for the four existing
  revalidation payload shapes; require exact boolean/status/issue invariants before returning
  `proven`, map unresolved observations to `blocked`/`not_proven`, and return `missing` for an
  unsupported or absent runtime-identity payload.
- Out of scope: changing persisted JSON, creating reviewer outcomes, runtime/provider/API/browser/
  Playwright/real-project execution, B6/C14 activation, or any medical conclusion.

## Success Criteria

- Current filesystem payloads derive to four non-proven statuses and never to `proven`.
- A proven status requires the exact source-specific readiness predicate, strict booleans, no issue
  rows and all authority flags false; malformed or unknown shapes fail closed as `missing`.
- Focused/adjacent/full monitoring tests pass, reserved ports stay empty and review-gate is clean.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- Direct Codex only; no delegated agent/provider.
- `proven` is returned only for source-specific structural proof; this helper does not verify file
  bytes or make medical/reviewer decisions. Runtime identity remains missing until a formal schema
  exists.
- Keep B6/C14 and 8911/5174/8910/4173 closed.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 10:38:44: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04 10:39:00: Static audit found the new assembler still accepted a caller-provided
  `status`; existing revalidation payloads expose different field-level proof predicates and
  runtime identity has no formal persisted schema, so generic status coercion would be unsafe.
- 2026-08-04: Added conservative source-specific derivation for B6, approved-input (three existing
  shapes), source-token and aggregate/CAS. Only exact proof predicates return `proven`; freshness,
  pending/blocking observations and generic runtime `verified` values cannot unlock a gate.
- 2026-08-04: Focused status-mapping/assembly/readiness/execution 53 passed; adjacent real-loop 96
  passed; full `tests/test_monitoring*.py` 1989 passed with 25 existing warnings (497.60s, rc 0).
  Current JSON mapping remained blocked/blocked/not_proven/blocked/missing. Final ports 8911/5174/
  8910/4173 were empty; records/review/metrics are ready for review-gate.
