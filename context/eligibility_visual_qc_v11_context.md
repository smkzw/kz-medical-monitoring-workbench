# Task Context: eligibility_visual_qc_v11

Created: 2026-07-11 21:12:50
Objective: Audit the implemented eligibility evidence visual-QC v11 backend for transactionality, evidence validity, API isolation, and regression risk
Task type: `code_open_audit`
Risk: `high`
Selected agent route: `reasonix-cli` / `deepseek-v4-pro` / `xhigh`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/sqlite_runtime_store.py`
- `services/api/app/eligibility.py`
- `services/api/app/eligibility_review_workflow.py`
- `packages/contracts/workbench_contracts/models.py`
- `packages/contracts/workbench_contracts/__init__.py`
- `tests/test_eligibility_visual_qc.py`
- `tests/test_sqlite_eligibility_review_store.py`
- `tests/test_eligibility_evidence_task_api.py`
- Main-venue review findings supplied in the current task: immutable QC records,
  CAS state, server-derived effective evidence, and no medical decision from QC.

## Scope

- In scope: read-only defect audit of the v11 implementation and tests.
- Out of scope: edits, VLM, frontend, live runtime migration, and clinical conclusions.

## Success Criteria

- Identify P0/P1 correctness or security defects with exact file/line references.
- Verify transactionality, idempotency, CAS, source/extraction/project isolation,
  effective evidence semantics, and API data minimization.
- Distinguish implementation defects from stale pre-v11 test expectations.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- QC sampled_pass is extraction/display quality only and must never imply medical
  verification, eligibility, electronic signature, or regulatory approval.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-11 21:12:50: Task initialized by `tools/hermes_workflow_guard.py init-task`.
