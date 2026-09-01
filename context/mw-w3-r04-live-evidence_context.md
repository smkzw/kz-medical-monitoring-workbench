# Task Context: mw-w3-r04-live-evidence

Created: 2026-07-24 23:39:54
Objective: Close W3 composite-adopt live evidence identity gaps with exact repository snapshot and catalog binding, add API success and stale-state counterexample tests, and preserve all existing behavior.
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/medical_writing_authoring_prefill.py`
- `services/api/app/main.py`
- `services/api/app/medical_writing_authoring_journey.py`
- `services/api/app/medical_writing_authoring_prefill_evidence.py`
- `services/api/app/medical_writing_authoring_prefill_evidence_binding.py`
- `tests/test_medical_writing_authoring_prefill_composite_adopt.py`
- `tests/test_medical_writing_authoring_prefill_composite_adopt_api.py`
- W3 r03 execution evidence:
  `runs/execution/mw_ai_first_candidate_packages_20260724/worker_w3_atomic_composite_adopt_03.md`

## Scope

- In scope: live package/catalog/candidate/snapshot identity binding, complete
  persisted-versus-live catalog equality, exact search-plan snapshot loading,
  API success and stale-state counterexamples.
- Out of scope: candidate generation semantics, PICOS model changes, frontend,
  competitor triage, DOCX generation, runtime restart.

## Success Criteria

- A valid two-path AI composite succeeds through the public API.
- Missing snapshot, switched search plan, package revision drift, and complete
  catalog content drift fail closed with HTTP 422 and no partial write.
- Existing pure override compatibility remains intact.
- The full W3 regression suite and Python compilation pass.

## Risk Boundaries

- Preserve the stable backend process until source and tests are accepted.
- Do not weaken W2b RFC6901, CT.gov field mapping, or atomic-leaf validation.
- This task was routed directly to Codex by the guard; no external-agent output
  is used as acceptance evidence.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-24 23:39:54: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-24 23:43: Added repository-backed live identity checks and five API
  counterexamples. Initial focused run exposed 14 service-test failures because
  the new live-state checks were also applied to the bounded no-resolver unit
  adapter; changed that adapter boundary without weakening the production API.
- 2026-07-24 23:44: Focused suite passed 62 tests plus 4 subtests.
- 2026-07-24 23:45: Full W3 suite passed 389 tests plus 52 subtests; flowchart
  regression passed 30 tests; frontend production build passed.
