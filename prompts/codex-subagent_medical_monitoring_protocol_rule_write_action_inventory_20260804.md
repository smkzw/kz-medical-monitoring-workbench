This task is reviewed directly by the parent Codex; no delegated subagent or
external provider is dispatched in the current turn.

The parent Codex owns the project contract, source authority, final verification,
production boundary and user delivery. Read and comply with workspace
`AGENTS.md`; do not route through Hermes or another external Agent.

Hard boundaries:
- Work only inside `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench`.
- Do not read or modify production paths unless the parent Codex explicitly authorizes them.
- Use available tools when they materially advance the bounded assignment; do not disable tools.
- Do not claim final clinical, regulatory, visual, browser, or user-facing acceptance authority.
- Runner-managed output path: `runs/codex-subagent_medical_monitoring_protocol_rule_write_action_inventory_20260804.md`. Do not write that report path with tools; return the complete handoff and let the runner persist it.

Read these files only:
- `context/medical_monitoring_protocol_rule_write_action_inventory_20260804_context.md`
- `services/api/app/medical_monitoring_router.py`
- `services/api/app/monitoring_identity_authorization.py`
- `services/api/app/monitoring_runtime_route_context.py`
- `services/api/app/monitoring_daily_run_router.py`
- the two lifecycle context files listed in the task context

Task:
Review the task context and produce a direct, bounded route-to-action
inventory. Do not edit product code, dispatch an agent, start services or run
real projects. Record the exact-action subset, policy-gap subset, high-risk
signature requirements, evidence and next action.

Output schema:
1. `# Codex SubAgent Task: medical_monitoring_protocol_rule_write_action_inventory_20260804`
2. `## Boundary Check`
3. `## Work Performed`
4. `## Evidence And Observations`
5. `## Verification And Gaps`
6. `## Next Action For Parent Codex`
