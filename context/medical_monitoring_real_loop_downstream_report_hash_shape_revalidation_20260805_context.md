# Task Context: medical_monitoring_real_loop_downstream_report_hash_shape_revalidation_20260805

Created: 2026-08-05 08:58:20
Objective: Harden downstream real-loop report and persisted acceptance-chain digest validation against silent normalization without runtime activation
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint
because it is a tracked, high-risk source integrity patch across downstream
real-loop report and persisted acceptance-chain boundaries.

## Source Of Truth

- `services/api/app/monitoring_real_loop_acceptance.py`
- `services/api/app/monitoring_real_loop_execution.py`
- `services/api/app/monitoring_real_loop_acceptance_revalidation.py`
- Their focused real-loop regression modules and current blocked gate.

## Scope

- In scope: exact lowercase 64-hex handling for downstream acceptance,
  execution and persisted revalidation report-chain digest fields; preserve
  blocked diagnostics and canonical report hashes.
- Out of scope: provider/runtime/browser/API login/real-project activity,
  medical-writing data, B6/C14 review, release activation and upstream
  readiness/route redesign.

## Success Criteria

- Present report-chain digests are never accepted after lower/strip rewriting
  or type coercion.
- Canonical report construction, assessment and persisted revalidation remain
  green; malformed chain values fail closed.
- Focused/adjacent tests, compileall, guard preflight and review gate pass;
  reserved ports remain empty.

## Risk Boundaries

- The authoritative gate is `read_only`/`blocked`; do not start services or
  ports 8911/5174/8910/4173, call providers, use browser/Playwright or API
  login, touch real projects/medical-writing data, or perform B6/C14/release
  activation.
- Product edits are limited to the three source modules and their focused
  regression modules. Codex owns verification and acceptance.

## Timeout Policy

- No delegated agent or provider is being launched; Codex owns this bounded
  source-only slice directly under the blocked runtime gate.

## Loop Log

- 2026-08-05 08:58:20: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05: Source audit found downstream acceptance/execution report
  constructors and assessment chain extraction using `_text`/`lower` before
  digest validation; persisted revalidation report fields had the same path.

## Next Safe Action

Patch only these downstream digest boundaries and focused negative regressions,
then recheck the authoritative gate. Formal source-token/CAS/host/runtime,
browser, real-project and medical-review actions remain blocked.

## Verification Result

- Focused acceptance/execution/revalidation suites: 51 passed in 0.17s.
- All real-loop contract suites: 142 passed in 0.42s.
- Changed modules compile; prompt preflight and review-gate passed with no
  warnings or errors.
- Ruff is unavailable; lint is unverified.
- Reserved ports 8911, 5174, 8910 and 4173 were empty.
- The authoritative real-loop gate remains read-only/blocked; no provider,
  runtime, browser, API login, real project or formal medical review occurred.
