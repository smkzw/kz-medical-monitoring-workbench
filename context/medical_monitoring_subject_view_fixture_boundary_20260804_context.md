# Task Context: medical_monitoring_subject_view_fixture_boundary_20260804

Created: 2026-08-04 21:29:37
Objective: Prevent buildSubjectView from implicitly falling back to demoSubjects when project-bound subject catalog is omitted; keep active monitoring path project-bound and source-only.
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `frontend/src/App.jsx` active monitoring subject-view construction and the three
  existing frontend monitoring contract files.
- `frontend/src/features/medical-monitoring/medicalMonitoringFixtures.mjs`
  remains compatibility-only fixture data; it must not be an implicit active-path
  fallback.
- Current gates and ports remain source-only/closed: B6 is fresh but pending
  formal review; C14/approved-input/host-identity and controlled runtime are not
  authorized.

## Scope

- In scope: change only `buildSubjectView`'s default `subjectCatalog` from the
  demo fixture to an empty list; add a source contract proving the default is
  project-neutral; update this task's evidence and review records.
- Out of scope: deleting compatibility fixtures or legacy components, changing
  API payloads/backend behavior, changing subject normalization, runtime,
  browser/Playwright/API-login, provider calls, SQLite, real projects, or
  medical-writing paths.

## Success Criteria

- An omitted subject catalog yields no demo subject injection, while explicit
  project-bound catalogs remain unchanged.
- Focused and adjacent frontend contracts, all monitoring Node contracts, and
  the Vite build pass; no required port is listening.
- Hermes review-gate for this slice is `ok=true` with no warnings/errors.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- Keep formal B6/C14/approved-input/host-identity and controlled five-project
  loop gates closed; offline tests cannot grant them.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 21:29:37: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04 21:30–21:34: Changed `buildSubjectView`'s default catalog to an
  empty list and added the static project-neutral fallback contract. Focused
  frontend contracts passed 35, adjacent contracts 71, all 32 monitoring Node
  contracts passed, Vite build passed, and required ports remained empty.
- 2026-08-04 21:34: Review-gate returned `ok=true` with no warnings/errors.
- 2026-08-04 21:35: Read-only adjacent readiness recheck passed: independent-AI
  generalization/evaluation/prompt-manifest contracts **17 passed** and
  structure-profile/shape/capability/admission contracts **31 passed**. These
  checks add no runtime or release authority.
