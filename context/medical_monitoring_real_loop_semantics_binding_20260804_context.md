# Task Context: medical_monitoring_real_loop_semantics_binding_20260804

Created: 2026-08-04 11:46:31
Objective: 离线绑定 evidence semantics snapshot 与 current manifest 的行级 identity、mapping hashes 与状态，保持 fail-closed
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Latest global/workspace/workbench `AGENTS.md` and current filesystem.
- LOOP 5.95 current manifest and LOOP 5.97 evidence-semantics snapshot, plus the new binding module
  and tests.
- Current status remains B6 `pending_review`, approved-input blocked, source-token fresh but
  `not_proven`, aggregate/CAS fresh but incomplete, runtime identity missing.

## Scope

- In scope: pure manifest↔semantic snapshot identity binding, deterministic derived binding record,
  focused/adjacent/full offline regression.
- Out of scope: rewriting either source snapshot, changing reviewer decisions, external signature or
  runtime/provider/API/browser/Playwright/real-project execution, B6/C14 activation or medical conclusions.

## Success Criteria

- Current binding is `matched` with zero issues; manifest report hash equals the snapshot source hash,
  snapshot hash recomputes, five row mapping-result hashes/statuses/semantic hashes match, and all
  authority flags remain false.
- Mutated hashes/statuses/rows/gates/issue counts/authority flags fail closed; compile/Ruff,
  focused/adjacent/full tests, JSON/cmp and port checks pass; review-gate is clean.

## Risk Boundaries

- Only source/tests/records/review/metrics plus `/private/tmp` logs are in scope; do not rewrite the
  manifest or semantic snapshot.
- Direct Codex only; no delegated agent/provider. The helper never reads paths or grants authority.
- Keep B6/C14 and 8911/5174/8910/4173 closed; existing non-reserved processes are not modified.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 11:46:31: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04 12:00: Added manifest↔semantics binding and generated the current binding record. It
  returned `matched`, issue_count `0`; focused 80, adjacent 123 and full 2016 passed, 25 warnings.
  The derived JSON matched temp output and reserved ports/latest AGENTS checks remained clean.
- Final Hermes `review-gate --require-verification` returned `{"ok": true, "warnings": [], "errors": []}`.
