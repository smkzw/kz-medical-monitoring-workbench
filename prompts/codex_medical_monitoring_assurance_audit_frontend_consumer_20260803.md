You are Codex executing this task directly. Ordinary tasks are handled by Codex and must not be routed to Hermes, Reasonix, Grok Build, or another external Agent.

Hard boundaries:
- Work only inside `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench`.
- Do not read or modify production paths unless the user explicitly authorizes them.
- Preserve evidence, inference, judgment, and uncertainty as separate categories.
- Runner-managed output path: `runs/codex_medical_monitoring_assurance_audit_frontend_consumer_20260803.md`. Never invoke a
  write/edit tool on this report path; return the complete report in your final
  response and let the runner persist it.

Read these files only:
- `context/medical_monitoring_assurance_audit_frontend_consumer_20260803_context.md`

Task:
Implement one bounded frontend slice in the medical-monitoring workbench.

## Objective

Expose the already implemented, server-authorized assurance audit read route
inside `MedicalMonitoringAssurancePanel` as a compact read-only chain. The panel
must help a senior medical monitor see what was done, when, under which task
version and hash binding, while never fabricating identity or permission.

## Sources to read

- `frontend/AGENTS.md` and the global/workspace AGENTS contracts.
- `frontend/src/features/medical-monitoring/medicalMonitoringAssuranceApi.mjs`
- `frontend/src/features/medical-monitoring/medicalMonitoringAssuranceView.mjs`
- `frontend/src/features/medical-monitoring/MedicalMonitoringAssurancePanel.jsx`
  and `.css`
- `frontend/src/features/medical-monitoring/medicalMonitoringPrincipal.mjs`
- `services/api/app/monitoring_assurance_router.py`
- `services/api/app/monitoring_audit_contract.py`
- existing assurance Node/static tests.

## Required changes

1. Add a `getAudit(projectId, taskId, { signal })` GET helper to the existing
   API factory. Do not add headers, tokens, actor fields or write methods.
2. Add strict `normalizeAssuranceAuditPayload` validation for the public route:
   project/task identity, non-empty verified `principal_id`, an array of event
   objects, ordered `event_hash`/`prev_event_hash` strings, known action and
   target fields, booleans, non-negative aggregate versions and ISO time. Do
   not render the payload or commit state if validation fails.
3. In the existing panel, fetch audit only for the selected task and only when
   `monitoringPrincipalReady(...)` is true. Use the existing project request
   scope and cancellation signal. Keep task/proof/rollup state visible if the
   audit request fails. Treat missing/expired/malformed principal as an
   identity-blocked state, not as empty audit history.
4. Render a compact `审计链` block in the selected-task detail. States must
   distinguish: no selected task, identity blocked, loading, API/read error,
   valid empty chain, and valid events. Show event order/action, occurred time,
   version transition and short event hash; do not show raw session ids,
   credentials or payload internals. No mutation button belongs here.
5. Add focused tests for API path and signal, valid/invalid audit payloads,
   project/task drift, and the panel static contract. Keep the desktop-first
   layout; only the dense audit list may scroll internally.

## Non-goals and gates

- Do not implement authentication/session middleware, client login, fallback
  principal, denied-attempt persistence, backend changes, schema changes,
  task/audit writes, App-wide refactor, service/browser/provider/API login,
  runtime DB or any real project.
- B6/C14, source/approved-input and Playwright/scientific/UAT gates remain
  closed. Do not claim runtime or commercial acceptance.

## Verification

Run focused Node tests for the changed assurance files, the existing frontend
contract tests covering project isolation and principal boundaries, Ruff or
equivalent static checks where applicable, and `frontend/npm run build` (or
the repository's exact build command). Check ports 8911/5174/8910/4173 remain
empty. Record exact commands/results and residual risks in the task records,
top-level review and metrics; pass the Hermes review-gate before continuing.

Output schema:
1. `# Codex Direct Task: medical_monitoring_assurance_audit_frontend_consumer_20260803`
2. `## Boundary Check`
3. `## Direct Work`
4. `## Evidence And Assumptions`
5. `## Verification`
6. `## Residual Risk`
