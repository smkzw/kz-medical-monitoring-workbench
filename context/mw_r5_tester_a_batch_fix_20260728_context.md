# Task Context: mw_r5_tester_a_batch_fix_20260728

Created: 2026-07-28 06:18:11
Objective: Consolidate Tester A six-perspective release-r5 blockers, implement minimal cross-indication repairs, and retest affected journeys without changing frozen evidence
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Frozen acceptance evidence under
  `runs/execution/mw_final_4x3_harness_20260727/rounds/release-r5-20260727/slots/A1`,
  `A2`, and `A3`, for both `lazy_medical_writer` and `engineer`.
- `DEFECTS.md`, `EXTERNAL_TESTER_REPORT.md`, `FIX_RETEST_LEDGER.md`,
  browser traces, pipeline lineage and terminal-state receipts in those six
  evidence directories.
- Current implementation under `frontend/src/features/medical-writing/`,
  `frontend/src/App.jsx`, `services/api/app/`, and the focused tests that
  exercise the same request/response contracts.
- Frozen release-r5 evidence is append-only acceptance evidence and must not be
  edited to make a later fix appear to have passed.

## Scope

- In scope: deduplicate the six reports; repair common product causes for
  A1 research-pipeline progress/scope, A2 synopsis terminal-state recovery,
  and A3 composite list-field adoption plus directly coupled UI state/
  idempotency defects; add focused deterministic tests; rerun affected clean
  browser journeys in a new repair round.
- Out of scope: unrelated subsystem changes, security or vulnerability audit,
  corpus-gate override, skeleton/placeholder PASS, changing the 12-scenario
  matrix, or editing historical release-r5 evidence.

## Success Criteria

- Each accepted defect has a source-backed root cause, minimal patch and
  regression test; tester-runtime defects remain separate from product fixes.
- A1 no longer presents false fixed ETA or forces an unbounded all-document
  preparation path before the user can continue with a medically relevant
  locked basket.
- A2 surfaces terminal AI timeout/failure in the visible import UI and offers a
  bounded retry/recovery path without duplicate work or a permanent spinner.
- A3 sends correctly typed list values, permits valid all-skipped adoption,
  avoids duplicate submissions, and preserves the active writing-journey
  location on refresh/reentry.
- Focused unit/contract tests and clean browser retests pass. A new immutable
  acceptance round is created after source changes; release-r5 is never
  retroactively marked PASS.

## Risk Boundaries

- Authorized writable product paths are limited to the workbench implementation
  and focused tests after the six-report consolidation is reviewed.
- Do not write to stable runtime data or frozen release-r5 evidence.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-28 06:18:11: Task initialized by `tools/hermes_workflow_guard.py init-task`.
