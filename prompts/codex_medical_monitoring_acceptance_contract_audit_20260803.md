You are Codex executing this task directly. Ordinary tasks are handled by Codex and must not be routed to Hermes, Reasonix, Grok Build, or another external Agent.

Hard boundaries:
- Work only inside `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench`.
- Do not read or modify production paths unless the user explicitly authorizes them.
- Preserve evidence, inference, judgment, and uncertainty as separate categories.
- Runner-managed output path: `runs/codex_medical_monitoring_acceptance_contract_audit_20260803.md`. Never invoke a
  write/edit tool on this report path; return the complete report in your final
  response and let the runner persist it.

Read these files only:
- `context/medical_monitoring_acceptance_contract_audit_20260803_context.md`
- `services/api/app/monitoring_real_loop_acceptance.py`
- `services/api/app/monitoring_real_loop_acceptance_revalidation.py`
- `services/api/app/monitoring_real_loop_readiness.py`
- `services/api/app/monitoring_real_loop_execution.py`
- `services/api/app/monitoring_real_loop_prompt_manifest.py`
- `tests/test_monitoring_real_loop_acceptance.py`
- `tests/test_monitoring_real_loop_acceptance_revalidation.py`
- `tests/test_monitoring_real_loop_readiness.py`
- `tests/test_monitoring_real_loop_execution.py`
- `tests/test_monitoring_real_loop_prompt_manifest.py`
- `records/active_slices/medical_monitoring_real_loop_readiness_contract_20260802/REAL_LOOP_READINESS.json`
- `records/active_slices/medical_monitoring_real_loop_acceptance_contract_20260802/ACCEPTANCE_CONTRACT.json`
- `records/active_slices/medical_monitoring_real_loop_acceptance_revalidation_20260803/REAL_LOOP_ACCEPTANCE_REVALIDATION.json`

Task:
Review the task context and complete the requested work directly. Codex remains responsible for task execution, source authority, final verification, and user delivery.

Do not start any runtime or generate real acceptance evidence. If the contract is structurally sound but intentionally does not verify external evidence-file content, document that as a residual gate rather than pretending synthetic refs are real evidence. Apply only a minimal fail-closed source fix if a concrete bypass is proven.

Output schema:
1. `# Codex Direct Task: medical_monitoring_acceptance_contract_audit_20260803`
2. `## Boundary Check`
3. `## Direct Work`
4. `## Evidence And Assumptions`
5. `## Verification`
6. `## Residual Risk`
