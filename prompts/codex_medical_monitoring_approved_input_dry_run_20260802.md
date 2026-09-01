You are Codex executing this task directly. Ordinary tasks are handled by Codex and must not be routed to Hermes, Reasonix, Grok Build, or another external Agent.

Hard boundaries:
- Work only inside `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench`.
- Do not read or modify production paths unless the user explicitly authorizes them.
- Preserve evidence, inference, judgment, and uncertainty as separate categories.
- Runner-managed output path: `runs/codex_medical_monitoring_approved_input_dry_run_20260802.md`. Never invoke a
  write/edit tool on this report path; return the complete report in your final
  response and let the runner persist it.

Read these files only:
- `context/medical_monitoring_approved_input_dry_run_20260802_context.md`

Task:
Review the task context and complete the requested work directly. Codex remains responsible for task execution, source authority, final verification, and user delivery.

The dry-run must distinguish readiness evidence from authority: even a
synthetic ready input may not set `write_permitted` or `migration_ready` true.
For the current package, do not infer missing reviewer outcomes, MY009 source
tokens or CAS expected versions; return explicit fail-closed issues.

Output schema:
1. `# Codex Direct Task: medical_monitoring_approved_input_dry_run_20260802`
2. `## Boundary Check`
3. `## Direct Work`
4. `## Evidence And Assumptions`
5. `## Verification`
6. `## Residual Risk`
