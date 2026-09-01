You are Codex executing this task directly. Ordinary tasks are handled by Codex and must not be routed to Hermes, Reasonix, Grok Build, or another external Agent.

Hard boundaries:
- Work only inside `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench`.
- Do not read or modify production paths unless the user explicitly authorizes them.
- Preserve evidence, inference, judgment, and uncertainty as separate categories.
- Runner-managed output path: `runs/codex_medical_monitoring_candidate_workflow_principal_gate_20260805.md`. Never invoke a
  write/edit tool on this report path; return the complete report in your final
  response and let the runner persist it.

Read these files only:
- `context/medical_monitoring_candidate_workflow_principal_gate_20260805_context.md`
- `services/api/app/monitoring_protocol_preparation_router.py`
- `services/api/app/monitoring_rule_template_recommendation_router.py`
- `services/api/app/monitoring_metric_configuration_router.py`
- `services/api/app/monitoring_runtime_principal.py`
- `services/api/app/monitoring_runtime_route_context.py`
- `services/api/app/monitoring_identity_authorization.py`
- `services/api/app/main.py`
- the focused router tests named by the context

Task:
Review the task context and complete the requested work directly. Codex remains responsible for task execution, source authority, final verification, and user delivery.

Implementation constraints:
- Follow the existing daily-run/assurance/metric route fail-closed pattern rather than
  inventing a token parser or fallback identity.
- Use explicit monitoring actions (`READ_MONITORING` for read status and
  `REVIEW_AI_CANDIDATE` for candidate workflow writes) and bind the canonical project,
  tenant, request ID, and verified principal before calling services.
- Preserve the offline test seam only as an explicit opt-out; never use it in `main.py`.
- Do not add runtime activation, persistence migrations, provider calls, or browser tests.

Output schema:
1. `# Codex Direct Task: medical_monitoring_candidate_workflow_principal_gate_20260805`
2. `## Boundary Check`
3. `## Direct Work`
4. `## Evidence And Assumptions`
5. `## Verification`
6. `## Residual Risk`
