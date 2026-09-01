You are Codex executing this task directly. Ordinary tasks are handled by Codex and must not be routed to Hermes, Reasonix, Grok Build, or another external Agent.

Hard boundaries:
- Work only inside `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench`.
- Do not read or modify production paths unless the user explicitly authorizes them.
- Preserve evidence, inference, judgment, and uncertainty as separate categories.
- Runner-managed output path: `runs/codex_medical_monitoring_b6_bridge_audit_20260803.md`. Never invoke a
  write/edit tool on this report path; return the complete report in your final
  response and let the runner persist it.

Read these files only:
- `context/medical_monitoring_b6_bridge_audit_20260803_context.md`
- `services/api/app/monitoring_b6_reviewer_packet_revalidation.py`
- `services/api/app/monitoring_b6_activation_gate.py`
- `services/api/app/monitoring_source_token_evidence_revalidation.py`
- `services/api/app/monitoring_aggregate_cas_replay.py`
- `services/api/app/monitoring_aggregate_cas_revalidation.py`
- `services/api/app/monitoring_disposition_chain_replay.py`
- `services/api/app/monitoring_approved_input_dry_run.py`
- `services/api/app/monitoring_runtime_principal.py`
- `services/api/app/monitoring_runtime_route_context.py`
- `services/api/app/monitoring_authorized_route_context.py`
- `tests/test_monitoring_b6_reviewer_packet_revalidation.py`
- `tests/test_monitoring_b6_activation_gate.py`
- `tests/test_monitoring_source_token_evidence_revalidation.py`
- `tests/test_monitoring_aggregate_cas_replay.py`
- `tests/test_monitoring_aggregate_cas_revalidation.py`
- `tests/test_monitoring_disposition_chain_replay.py`
- `tests/test_monitoring_approved_input_dry_run.py`
- `tests/test_monitoring_runtime_principal.py`
- `tests/test_monitoring_runtime_route_context.py`
- `tests/test_monitoring_identity_authorization.py`

Task:
Review the task context and complete the requested work directly. Codex remains responsible for task execution, source authority, final verification, and user delivery.

Do not create reviewer outcomes, modify gate packets, synthesize source tokens or CAS versions, start any runtime, or claim commercial readiness. If a code defect is proven, apply only the smallest fail-closed correction inside the workbench and test it; otherwise leave source unchanged.

Output schema:
1. `# Codex Direct Task: medical_monitoring_b6_bridge_audit_20260803`
2. `## Boundary Check`
3. `## Direct Work`
4. `## Evidence And Assumptions`
5. `## Verification`
6. `## Residual Risk`
