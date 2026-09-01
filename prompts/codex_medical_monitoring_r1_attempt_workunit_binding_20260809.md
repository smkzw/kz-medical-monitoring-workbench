You are Codex executing this task directly. Ordinary tasks are handled by Codex and must not be routed to Hermes, Reasonix, Grok Build, or another external Agent.

Hard boundaries:
- Work only inside `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench`.
- Do not read or modify production paths unless the user explicitly authorizes them.
- Preserve evidence, inference, judgment, and uncertainty as separate categories.
- Runner-managed output path: `runs/codex_medical_monitoring_r1_attempt_workunit_binding_20260809.md`. Never invoke a
  write/edit tool on this report path; return the complete report in your final
  response and let the runner persist it.

Read these files only:
- `context/medical_monitoring_r1_attempt_workunit_binding_20260809_context.md`
- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md`
- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md`
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/domain.py`
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/store.py`
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/capability_runtime.py`
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/adapters.py`
- `poc/medical_monitoring_ai_native_r1/tests/test_authoritative_progress.py`
- `poc/medical_monitoring_ai_native_r1/tests/test_capability_runtime.py`
- `poc/medical_monitoring_ai_native_r1/docs/R1_AUTHORITATIVE_PROGRESS_EVIDENCE.md`

Task:
Implement the bounded schema-v6 capability-attempt/work-unit binding described in the task
context. Keep the implementation framework-neutral and synthetic/offline. Preserve deterministic
work-unit compatibility, bind AI progress only from the application-owned attempt journal,
support a validated continuation chain, fail closed on non-success terminal outcomes, and add
focused corruption/migration/retry tests. Do not build the controller or UI in this task.

Output schema:
1. `# Codex Direct Task: medical_monitoring_r1_attempt_workunit_binding_20260809`
2. `## Boundary Check`
3. `## Direct Work`
4. `## Evidence And Assumptions`
5. `## Verification`
6. `## Residual Risk`
