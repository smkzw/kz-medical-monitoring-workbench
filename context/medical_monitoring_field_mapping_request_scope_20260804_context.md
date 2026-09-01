# Task Context: medical_monitoring_field_mapping_request_scope_20260804

Created: 2026-08-04 21:12:52
Objective: Add project-bound request lifecycle and cancellation to the medical-monitoring field mapping panel so project switches and panel closure cannot commit stale mapping responses.
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `frontend/src/features/medical-monitoring/MedicalMonitoringFieldMappingPanel.jsx` — field mapping status, AI mapping, edit and confirmation requests.
- `frontend/src/features/medical-monitoring/medicalMonitoringProjectRequestScope.mjs` — project-bound cancellation/activation semantics.
- `tests/test_frontend_monitoring_contract.py` — static lifecycle contract.
- Current workbench filesystem and applicable global/workbench `AGENTS.md` files.
- B6/C14/approved-input/host-attestation/runtime/provider/browser/real-project gates remain closed; ports 8911, 5174, 8910 and 4173 must remain empty.

## Scope

- In scope: add a project-bound request scope to the field mapping panel, pass abort signals to all reads/mutations, guard state commits with `isCurrent`, and cancel status polling on cleanup.
- Out of scope: API/service/storage changes, field-mapping semantics, B6/C14, approved-input or identity gates, runtime/provider/browser/Playwright/API login, real projects, databases and medical-writing.

## Success Criteria

- Activation/disposal is established before the initial status request.
- Status, start, adopt, edit and confirm requests are cancellable and cannot commit after project disposal/supersession.
- Focused/adjacent contracts, all monitoring Node contracts and Vite build pass; no gate or port state changes.

## Finding And Decision

Unlike the batch, daily-run and assurance panels, field mapping used direct API promises with a boolean unmount guard only. A project switch or panel close could leave requests running and a polling refresh could race a newer response. The repair adopts the existing shared request-scope primitive without changing endpoint payloads or mapping decisions.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 21:12:52: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04 21:10–21:13: Added project-bound request scope, abort signals, current-request guards and cleanup cancellation; static/Node/build checks passed.
- 2026-08-04 21:13: Status polling is explicitly cancelled before a new mapping start to prevent an old status response from overwriting the new run; full offline regression remains green.
