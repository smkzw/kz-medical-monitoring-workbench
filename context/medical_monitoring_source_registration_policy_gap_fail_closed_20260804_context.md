# Task Context: medical_monitoring_source_registration_policy_gap_fail_closed_20260804

Created: 2026-08-04 05:46:42
Objective: 为 legacy source registration 与 eligibility source-admission 写入入口增加 server principal/project scope 后的显式 fail-closed policy-gap，禁止未命名动作调用 SourceRegistryService；不新增 action/role，不改 medical-writing 专用上传、service contract、DB 或 runtime
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/main.py` source-registration and eligibility source-admission
  handlers; `_reject_legacy_monitoring_policy_gap` and
  `_authorize_legacy_monitoring_action` are the existing fail-closed helpers.
- `services/api/app/source_intake.py` and source-registry tests for the direct
  service contracts and public-field redaction.
- `tests/test_source_registry.py`, `tests/test_source_content_validation.py`,
  `tests/test_canonical_project_context.py`, and current P10/B6/C14 records.
- Existing action matrix in `services/api/app/monitoring_action_authorization.py`:
  no exact source-registration or source-admission write action exists.

## Scope

- In scope: the legacy HTTP writes
  `eligibility/source-admission/refresh`, `sources/protocol-docx`,
  `sources/listing-file`, `sources/raw-subject-bundle`, `sources/local-file`,
  `sources/local-directory`, and `sources/local-candidate`. Each must verify
  server principal/project scope and then return the explicit
  `monitoring_write_action_unconfigured` policy-gap response before calling
  `SourceRegistryService` or a configured local path. Add no new action/role.
- In scope: update focused API regressions so missing identity returns 503,
  scoped identity returns 403, and patched registries are not called; retain
  direct source-registry/admission service tests.
- Out of scope: medical-writing investigator-brochure upload, generic project
  creation, service/repository contracts, frontend, DB/schema/migration,
  auth middleware/provider, runtime database, provider/browser/API login,
  external models, real projects, and B6/C14 activation.

## Success Criteria

- No-principal requests fail with `monitoring_principal_unavailable` 503.
- A valid project-scoped server principal receives 403 with
  `monitoring_write_action_unconfigured`; source registry and local-path
  services are not called.
- Direct registry and admission service behavior remains covered.
- Targeted compile/focused tests, full monitoring suite, and Hermes
  review-gate pass; reserved ports remain stopped/empty.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 05:46:42: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04: Inventory confirmed these are state-changing local-source
  registration/admission paths with no semantically exact action; explicit
  denial is safer than reusing `INTAKE_BATCH` or a read action.
