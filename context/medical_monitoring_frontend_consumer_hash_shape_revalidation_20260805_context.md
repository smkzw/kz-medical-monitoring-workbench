# Task Context: medical_monitoring_frontend_consumer_hash_shape_revalidation_20260805

Created: 2026-08-05 07:41:38
Objective: Harden the frontend clinical consumer contract to reject uppercase, padded, non-string, and malformed SHA-256 handoff/event digests without normalization, matching the backend source-preserving boundary, with focused Node regressions.
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `frontend/src/features/medical-monitoring/medicalMonitoringConsumerContract.mjs`
- `frontend/src/features/medical-monitoring/medicalMonitoringConsumerContract.test.mjs`
- Backend counterpart:
  `services/api/app/monitoring_clinical_consumer_handoff.py`.
- Current P10/B6/C14 gate records; the real-loop gate remains read-only and
  blocked.

## Scope

- In scope: exact lowercase SHA-256 shape validation for frontend clinical
  consumer handoff/event digests; focused Node regressions and source-only
  evidence.
- Out of scope: clinical inference, backend changes, API/provider/browser
  activation, real projects, medical-writing data, B6/C14 and release claims.

## Success Criteria

- Uppercase, padded, non-string and malformed digest values fail closed in the
  frontend consumer; valid lowercase values and existing conservation checks
  remain green.
- Focused and adjacent frontend tests pass; no service/port/browser/provider
  activity occurs.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- Keep 8911, 5174, 8910 and 4173 stopped; do not use Playwright or real data.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 07:41:38: Task initialized by `tools/hermes_workflow_guard.py init-task`.
