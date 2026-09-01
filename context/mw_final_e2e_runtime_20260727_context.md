# Task Context: mw_final_e2e_runtime_20260727

Created: 2026-07-27 05:38:31
Objective: Build fail-closed per-run isolated backend/frontend service orchestrator for locked final 4x3 medical-writing E2E matrix; no external tester models, no shared runtime writes, no product code changes.
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `scripts/qc/mw_final_4x3_harness.py`
- `scripts/qc/mw_isolated_runtime_baseline.py`
- `prompts/final_4x3_e2e_20260727/CLEAN_STATE_BACKUP_RESET_CHECKLIST.md`
- `prompts/final_4x3_e2e_20260727/PER_SLOT_COMPLETION_SCHEMA.json`
- `packages/contracts/workbench_contracts/runtime_contract.json`
- The locked run root:
  `runs/execution/mw_final_4x3_harness_20260727`

## Scope

- In scope: a strict per-round/slot/perspective API/Vite service orchestrator,
  clean-state-before-frontend sequencing, localhost port isolation, secret-free
  receipts, status/stop and deterministic failure-closed tests.
- Out of scope: external tester/model launch, product source changes, shared
  runtime mutation, PASS creation, deletion or reuse of failed rounds, browser
  actions and product workflow execution.

## Success Criteria

- A new run calls the accepted baseline prepare implementation.
- API uses the locked Xcode Python 3.9 with `PYTHONPATH` removed and the exact
  isolated runtime/reference-project environment.
- `CLEAN_STATE_RECEIPT.json` exists at mode `0600` before Vite starts.
- `/runtime-build.json`, direct backend readiness and Vite-proxied backend
  readiness agree on the runtime/API/build contract.
- `SERVICE_RECEIPT.json` is atomic, mode `0600`, secret-free, and contains only
  test PID/port/command summaries and a runtime identity hash.
- `status` is read-only. `stop` validates PID identity and port ownership before
  signaling only receipt PIDs, then proves both ports are free.
- Symlinks, adjacent-prefix paths, shared runtimes, stable ports 5174/8911,
  occupied/duplicate ports and any prior receipt/runtime fail closed.

## Risk Boundaries

- Do not write shared runtime, stable service state or product code.
- Never launch external tester models from this tool.
- Never create PASS evidence or delete a prior failed run.
- Test-only root overrides must resolve to an explicit system-temporary root.
- All process termination must be receipt-scoped and PID-reuse-safe.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-27 05:38:31: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-27 05:41 CST: Implemented the first strict orchestrator and fake
  process/temp-root tests.
- 2026-07-27 05:45 CST: Focused baseline/harness/orchestrator regression passed
  `57/57`; repaired the Xcode Python leaf-symlink exception without weakening
  state-path symlink rejection.
- 2026-07-27 05:48 CST: Real temp-root API/Vite probe passed start, status,
  contract, receipt and stop gates; shared configuration hashes were unchanged.
- 2026-07-27 05:50 CST: Added lock-file symlink fail-close coverage; final
  focused regression passed `58/58`.
