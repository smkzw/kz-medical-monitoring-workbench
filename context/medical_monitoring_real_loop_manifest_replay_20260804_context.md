# Task Context: medical_monitoring_real_loop_manifest_replay_20260804

Created: 2026-08-04 11:15:39
Objective: 离线重放当前 real-loop gate manifest 的 artifact/payload/result hashes，发现源文件漂移并保持 fail-closed
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Latest global/workspace/workbench `AGENTS.md` and current filesystem.
- `services/api/app/monitoring_real_loop_current_manifest.py`, status mapping and upstream assembly
  modules/tests.
- Current derived snapshot
  `records/active_slices/medical_monitoring_real_loop_current_manifest_20260804/CURRENT_REAL_LOOP_GATE_MANIFEST.json`
  and its four source JSONs: B6 review gate, approved-input source binding, source-token evidence
  revalidation and aggregate/CAS revalidation.
- Current truth remains B6 `pending_review`, C14 `blocked_pending_b6_review`, approved-input blocked,
  source-token `not_proven`, aggregate/CAS replay incomplete and runtime identity missing.

## Scope

- In scope: a pure replay contract that receives source bytes/payloads explicitly, recomputes artifact,
  canonical payload and mapping-result hashes, compares the persisted current manifest and returns a
  deterministic fail-closed report; focused tests and offline regression.
- Out of scope: reading arbitrary paths inside the module, rewriting source gate JSONs or the manifest,
  changing reviewer decisions, runtime/provider/API/browser/Playwright/real-project execution,
  B6/C14 activation or medical conclusions.

## Success Criteria

- Current four JSON bytes plus explicit runtime-missing row replay to `matched` with overall manifest
  still `blocked`, all authority flags false and no replay issues.
- Mutated bytes, payload, row hash, manifest report hash, missing source or authority-bearing manifest
  fail closed with a precise issue and no permission becomes true.
- Focused/adjacent/full monitoring tests, compile/Ruff, JSON replay and reserved-port checks pass;
  review-gate is clean.

## Risk Boundaries

- Do not write original gate JSONs, runtime data or controlled paths; only source/tests/records/review
  artifacts in the workbench are in scope.
- Direct Codex only; no delegated agent/provider. The replay helper never reads paths and cannot grant
  runtime/provider/write authority.
- Keep B6/C14 and 8911/5174/8910/4173 closed; existing non-reserved processes are not modified.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 11:15:39: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04 11:16: reviewed the LOOP 5.95 manifest contract. The next bounded change is to add
  an explicit bytes/payload/result hash replay function rather than treating a persisted manifest as
  self-authenticating evidence.
- 2026-08-04 11:30: added `monitoring_real_loop_manifest_replay.py` and its focused tests. Current
  source bytes/payloads replayed to `matched`, issue_count `0`; mutation and missing-source cases
  return `blocked`. Focused **67**, adjacent **110**, full **2003 passed, 25 warnings, 485.14s**;
  compile/Ruff and reserved-port checks pass. Review/metrics/task record written; final review-gate
  remains to be run after record closure.
- Final Hermes `review-gate --require-verification` returned `{"ok": true, "warnings": [], "errors": []}`.
