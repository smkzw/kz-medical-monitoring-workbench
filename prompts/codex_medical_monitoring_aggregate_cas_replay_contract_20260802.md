You are Codex executing this task directly. Ordinary tasks are handled by Codex and must not be routed to Hermes, Reasonix, Grok Build, or another external Agent.

Hard boundaries:
- Work only inside `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench`.
- Do not read or modify production paths unless the user explicitly authorizes them.
- Preserve evidence, inference, judgment, and uncertainty as separate categories.
- Runner-managed output path: `runs/codex_medical_monitoring_aggregate_cas_replay_contract_20260802.md`. Never invoke a
  write/edit tool on this report path; return the complete report in your final
  response and let the runner persist it.

Read these files only:
- `context/medical_monitoring_aggregate_cas_replay_contract_20260802_context.md`
- `services/api/app/medical_risk_authority.py`
- `services/api/app/monitoring_disposition_chain_replay.py`
- `runs/execution/medical_monitoring_phase_b4_residual_decision_20260801/B4_RESIDUAL_DECISION_PACKAGE.json`

Implement only the bounded pure in-memory contract and focused tests described
in the context. Do not write the runner-managed report path or any runtime/
production store. Replay actual B4 metadata only as a diagnostic and do not
invent missing `expected_version` values as observed facts.

Task:
Review the task context and complete the requested work directly. Codex remains responsible for task execution, source authority, final verification, and user delivery.

Output schema:
1. `# Codex Direct Task: medical_monitoring_aggregate_cas_replay_contract_20260802`
2. `## Boundary Check`
3. `## Direct Work`
4. `## Evidence And Assumptions`
5. `## Verification`
6. `## Residual Risk`
