You are Codex executing this task directly. Ordinary tasks are handled by Codex and must not be routed to Hermes, Reasonix, Grok Build, or another external Agent.

Hard boundaries:
- Work only inside `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench`.
- Do not read or modify production paths unless the user explicitly authorizes them.
- Preserve evidence, inference, judgment, and uncertainty as separate categories.
- Runner-managed output path: `runs/codex_medical_monitoring_ai_router_principal_gate_20260805.md`. Never invoke a
  write/edit tool on this report path; return the complete report in your final
  response and let the runner persist it.

Read these files only:
- `context/medical_monitoring_ai_router_principal_gate_20260805_context.md`
- `services/api/app/monitoring_ai_router.py`
- `services/api/app/monitoring_metric_configuration_router.py`
- `services/api/app/monitoring_runtime_principal.py`
- `services/api/app/monitoring_runtime_route_context.py`
- `services/api/app/monitoring_identity_authorization.py`
- `services/api/app/main.py`
- the focused AI API tests named by the context

Task:
Review the task context and complete the requested work directly. Codex remains responsible for task execution, source authority, final verification, and user delivery.

Implementation constraints:
- Follow the existing metric/daily-run/assurance host-principal fail-closed
  seam. Do not parse bearer tokens, cookies, headers, or client actor values.
- Keep action mapping explicit: evidence/source reads use a source/read action;
  job/status reads use `READ_AI_RUN` or an equally explicit existing read
  action; candidate/mapping job writes use `REVIEW_AI_CANDIDATE` (the existing
  action that covers AI candidate workflows) unless a more precise existing
  action is demonstrably required.
- Server-derived identity must replace request `actor`/`confirmed_by` values
  before repository/service calls. `require_server_principal=False` is only
  for isolated offline tests.
- Do not start any service/provider/browser or invoke real projects.

Output schema:
1. `# Codex Direct Task: medical_monitoring_ai_router_principal_gate_20260805`
2. `## Boundary Check`
3. `## Direct Work`
4. `## Evidence And Assumptions`
5. `## Verification`
6. `## Residual Risk`
