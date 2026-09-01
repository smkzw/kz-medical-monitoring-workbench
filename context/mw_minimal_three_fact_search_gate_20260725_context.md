# Task Context: mw_minimal_three_fact_search_gate_20260725

Created: 2026-07-25 02:22:08
Objective: Make drug + indication + phase the only hard gate for competitor ClinicalTrials.gov search while preserving strict downstream protocol-candidate readiness
Task type: `code_scoped_patch_plan`
Risk: `medium`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- User contract dated 2026-07-25 in the active Codex thread.
- Global `/Users/smkzw/.codex/AGENTS.md`, project `AGENTS.md`, and
  `records/active_slices/medical_writing_authoring_journey_20260714/TASK_RECORD.md`.
- Current contracts, service, authoring journey frontend, and focused tests in this workbench.

## Scope

- In scope: minimal three-fact competitor-search readiness, draft-aware search
  planning/execution, synopsis-path consistency, UI required-state correction,
  backward compatibility, tests and review record.
- Out of scope: `main.py`, translation/upper-layer code, stable service lifecycle,
  real ClinicalTrials.gov calls, real model calls, unrelated frontend prefill refactors.

## Success Criteria

- Drug + indication + phase creates an executable search plan.
- Missing any one of those facts blocks search.
- Optional framing remains unconfirmed and can be populated from later evidence.
- A search snapshot is consumable by downstream prefill.
- Existing payloads remain compatible and the UI presents no extra initial hard gate.

## Risk Boundaries

- Write only directly related contracts, authoring service/journey frontend,
  tests, task records and required review artifacts.
- Do not modify `main.py`, translation/upper-layer files, restart services,
  call ClinicalTrials.gov, or invoke a real model.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-25 02:22:08: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-25 02:27-02:36: Implemented and corrected draft-aware three-fact
  planning while preserving committed framing and unconfirmed field states.
- 2026-07-25 02:36: Backend adjacent suite 154 passed; focused frontend
  contract 3 passed; Python compile and Vite production build passed.
- 2026-07-25 02:37: Initially recorded the pre-existing full frontend static
  failure for `LOW_RISK_BATCH_PREFILL_FIELDS` without changing business code.
- 2026-07-25 follow-up: Main-venue review proved that assertion set stale
  against the accepted W4 atomic composite-adopt contract and the current
  three-fact condition fallback. Updated only the test contract and records;
  full frontend contract now 99 passed, W4 deterministic QC and Vite build passed.
