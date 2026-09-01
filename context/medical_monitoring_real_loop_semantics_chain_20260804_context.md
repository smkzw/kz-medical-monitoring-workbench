# Task Context: medical_monitoring_real_loop_semantics_chain_20260804

Created: 2026-08-04 12:12:59
Objective: 贯通 RealLoopReadiness semantic binding hash/matched 至 execution、acceptance 与 persisted revalidation，保持证据链 fail-closed
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_real_loop_readiness.py`
- `services/api/app/monitoring_real_loop_execution.py`
- `services/api/app/monitoring_real_loop_acceptance.py`
- `services/api/app/monitoring_real_loop_acceptance_revalidation.py`
- the focused tests for those four modules under `tests/`
- the current LOOP5.99 semantic binding artifact and gate manifest

## Scope

- In scope: propagate the exact `semantics_binding_sha256` through execution,
  acceptance, and persisted acceptance revalidation; advance payload schemas;
  add fail-closed missing/malformed/mutated-hash coverage and records.
- Out of scope: service or port startup, providers, browser/Playwright, real
  projects, B6/C14 activation, migrations, application writes, and any medical
  or release decision.

## Success Criteria

1. A complete synthetic chain carries the exact lowercase semantic-binding hash
   through execution, acceptance, and persisted acceptance revalidation.
2. Missing, malformed, changed, and legacy payloads fail closed with explicit
   deterministic issue codes and no authority flags.
3. Focused, adjacent, and full workbench tests pass after all three modules are
   updated.
4. Review-gate, metrics, test-evidence, and LOOP-ledger records preserve the
   result and next safe action.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 12:12:59: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- Recovery boundary: if interrupted, re-read this context plus the four modules
  and tests; finish this contract slice before inferring any advancement of
  B6/C14 or real-project acceptance.
- 2026-08-04 12:49: Semantic hash propagation completed; direct 44/44, adjacent 129/129,
  monitoring 2022/2022; review-gate passed. Full-workbench baseline remains non-green outside
  this slice. No runtime/provider/browser/project action occurred.
