# Task Context: medical_monitoring_source_batch_five_project_alignment_20260803

Created: 2026-08-03 22:01:57
Objective: Align read-only source-batch preflight and approved-input default project coverage with the five-project real-loop contract while preserving fail-closed evidence
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_real_loop_acceptance.py` and `monitoring_real_loop_readiness.py` (five-project contract).
- `services/api/app/monitoring_source_batch_preflight.py` and `monitoring_source_batch_preflight_revalidation.py`.
- `services/api/app/monitoring_approved_input_dry_run.py` default `required_project_ids` binding.
- Existing real source preflight evidence under `records/active_slices/medical_monitoring_real_source_batch_preflight_20260803/` and approved-input source-binding evidence.
- Current B6/C14/source-token/CAS/real-loop gates remain blocked and must not be mutated.

## Scope

- In scope: replace the stale three-project source-preflight default with the five opaque project IDs already fixed by the real-loop contract; update contract/docs/tests and re-run the actual diagnostic preflight/revalidation paths.
- Out of scope: source promotion, batch creation, project imports, parser changes, provider/runtime/browser/API login, SQLite/risk/disposition writes, B6/C14/CAS/source-token changes, medical/UAT/release decisions.

## Success Criteria

- Default source-batch and controlled approved-input preflight require exactly five projects and never treat missing MY008 evidence as complete.
- Existing synthetic contract fixtures cover all five projects and pass; current filesystem evidence remains `blocked` with explicit missing/insufficient evidence rather than being promoted.
- Focused source/preflight/approved-input/readiness/release tests, Ruff/compile checks and listener checks pass.
- No runtime or project state is changed.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-03 22:01:57: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-03 22:10:00: Changed the source-preflight canonical default to the five-project real-loop set, updated the synthetic row-count assertion, ran 47 focused tests plus Ruff/compileall, and passed prompt preflight.
- 2026-08-03 22:10:00: Replayed the current persisted real-source envelope read-only. It is byte-fresh but stale against the five-project policy and remains blocked; no historical artifact was rewritten. Review-gate passed. Next action is upstream B6 outcome validation, not runtime.
