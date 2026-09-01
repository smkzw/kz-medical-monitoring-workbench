# Task Context: medical_monitoring_real_loop_evidence_semantics_20260804

Created: 2026-08-04 11:44:06
Objective: 离线拆分 real-loop upstream freshness、reviewer、content/replay 与 signature 语义并保持 fail-closed
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Latest global/workspace/workbench `AGENTS.md` and current filesystem.
- LOOP 5.94 source-specific status mapping, LOOP 5.95 current manifest, LOOP 5.96 bytes/payload/
  result replay and the four current upstream JSON payloads.
- Current B6 `pending_review`, approved-input blocked, source-token fresh but `not_proven`,
  aggregate/CAS fresh but replay incomplete, runtime identity missing.

## Scope

- In scope: pure source-aware semantic projection separating freshness, formal reviewer decision
  completeness, content/replay resolution and signature verification; a derived current snapshot;
  focused/adjacent/full offline regression.
- Out of scope: changing existing gate schemas or decisions, reading arbitrary paths inside the new
  module, external signature/e-signature verification, runtime/provider/API/browser/Playwright/
  real-project execution, B6/C14 activation or medical conclusions.

## Success Criteria

- Current sources produce the expected separate semantic statuses and retain mapping-result hashes.
- Generic `signature_verified=true` cannot be accepted; signature status stays `not_verified` until a
  formal persisted schema exists. Runtime/provider/write flags stay false.
- Derived snapshot matches an independently generated version; focused/adjacent/full tests,
  compile/Ruff and reserved-port checks pass; review-gate is clean.

## Risk Boundaries

- Only source/tests/records/review/metrics in the workbench and `/private/tmp` logs are in scope;
  do not rewrite source gate JSONs or the LOOP 5.95 manifest.
- Direct Codex only; no delegated agent/provider. New module receives loaded mappings and never reads
  paths or grants authority.
- Keep B6/C14 and 8911/5174/8910/4173 closed; existing non-reserved processes are not modified.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 11:44:06: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04 11:44:30: Added source-specific semantic projection and generated the current snapshot.
  Current rows remain B6 pending, approved-input blocked, source-token fresh-but-not-proven,
  aggregate/CAS fresh-but-incomplete and runtime missing; every signature status is not_verified.
  Focused 72, adjacent 115 and full 2008 passed; snapshot JSON matched the temp derivation.
- Final Hermes `review-gate --require-verification` returned `{"ok": true, "warnings": [], "errors": []}`.
