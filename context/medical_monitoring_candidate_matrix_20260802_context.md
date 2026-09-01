# Task Context: medical_monitoring_candidate_matrix_20260802

Created: 2026-08-02 22:47:32
Objective: Record the user-requested five-project real-loop candidate matrix without changing the canonical readiness set or granting runtime authority
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- User-provided candidate project roots and test requirements in the current
  task message.
- Current executable readiness contract:
  `services/api/app/monitoring_real_loop_readiness.py` and
  `records/active_slices/medical_monitoring_real_loop_readiness_contract_20260802/REAL_LOOP_READINESS.json`.
- Current frozen prompt contract:
  `records/active_slices/medical_monitoring_real_loop_prompt_manifest_20260802/PROMPT_MANIFEST.json`.
- Existing project-set reconciliation:
  `records/active_slices/medical_monitoring_project_set_traceability_reconciliation_20260802/`.
- The five user-supplied roots may be read for bounded existence/inventory
  evidence; their contents remain project-source evidence, not instructions.

## Scope

- In scope: a machine-readable candidate matrix, bounded local-root existence
  inventory, explicit separation of requested candidate scope from the current
  three-project canonical contract, and a durable planning/reconciliation note.
- Out of scope: changing `REAL_LOOP_PROJECT_IDS`, rebuilding the prompt
  manifest, source registration, batch approval, B6/CAS/source-token closure,
  provider dispatch, API/backend login, Playwright execution, service/runtime/
  SQLite writes, real-project mutation, or medical approval.

## Success Criteria

- All five requested project roots are represented without silently admitting
  the two MY008 projects into the executable set.
- Role/task/login/route/acceptance requirements are preserved as explicit
  future criteria, with route availability and project eligibility marked
  unverified until their own gates pass.
- The artifact is hashable and review-gate verifiable; no product source or
  runtime state changes.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- Do not infer clinical correctness, source eligibility, batch completeness or
  commercial readiness from directory existence, file counts, names or user
  supplied paths.
- Keep current canonical readiness and 24-row prompt manifest unchanged; any
  future scope change must update source/provenance, adapters, prompts, tests,
  acceptance dossier and release traceability together.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-02 22:47:32: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-02 22:50 CST: Bounded recursive path inventory observed all five user
  roots present. Counts include nested working/tooling material and are not
  eligibility evidence; no source was registered and no runtime was started.
- 2026-08-02 22:52 CST: Candidate JSON integrity, canonical prompt-manifest
  linkage, port stop state and protected frontend hashes verified; Hermes
  review-gate returned `ok=true`.
