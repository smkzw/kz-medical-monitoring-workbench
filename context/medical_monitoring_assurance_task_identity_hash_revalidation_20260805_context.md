# Task Context: medical_monitoring_assurance_task_identity_hash_revalidation_20260805

Created: 2026-08-05 01:33:36
Objective: Revalidate persisted assurance task frozen identity hash on restart reads
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_assurance_repository.py`
- `tests/test_monitoring_assurance.py`
- adjacent assurance principal, module-contract and release gate/dossier tests
- current P10 completion matrix and release gate audit

## Scope

- In scope: normalize persisted frozen task identity, recompute and verify its
  stored identity hash on restart reads, and add a semantically-valid tamper
  regression.
- Out of scope: medical inference, runtime startup, provider/browser/Playwright,
  real projects, B6/C14, migrations, UI or medical-writing files.

## Success Criteria

- A persisted task with a semantically valid but hash-mismatched frozen
  identity cannot be read or used for further assurance transitions.
- Existing malformed-field diagnostics and assurance/release contracts remain
  precise; focused/adjacent tests, compile and Ruff pass.
- No authority or activation flag changes.

## Risk Boundaries

- Do not start or connect to 8911, 5174, 8910 or 4173; do not touch runtime
  databases or real projects.
- No external model dispatch; Codex remains final authority.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 01:33:36: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05 01:34: source audit found `_task_from_row` parsed frozen identity
  JSON without comparing the stored `identity_hash`; source patch and focused
  regression were applied and offline tests passed. Runtime gates remain closed.
- 2026-08-05 01:35-01:38: normalized frozen identity and added canonical hash
  revalidation; focused 30 and adjacent 178 tests passed, compileall and Ruff
  passed, and review-gate returned `ok=true`. Runtime, provider, browser and
  real-project gates remain closed.
