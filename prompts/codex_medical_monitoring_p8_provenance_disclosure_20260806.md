You are Codex executing this task directly. Ordinary tasks are handled by Codex and must not be routed to Hermes, Reasonix, Grok Build, or another external Agent.

Hard boundaries:
- Work only inside `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench`.
- Do not start services, reserved ports, providers, browsers, Playwright, API
  login or real-project runs.
- Preserve the `read_only / blocked` real-loop gate and the medical-writing
  subsystem.
- Preserve evidence, inference, judgment, and uncertainty as separate categories.
- Runner-managed output path: `runs/codex_medical_monitoring_p8_provenance_disclosure_20260806.md`. Never invoke a
  write/edit tool on this report path; return the complete report in your final
  response and let the runner persist it.

Read these files only:
- `context/medical_monitoring_p8_provenance_disclosure_20260806_context.md`

Task:
Review the task context and complete the requested work directly. Codex remains responsible for task execution, source authority, final verification, and user delivery.

Implement only a compact collapsed P8 provenance disclosure. It must appear for
an explicitly `mixed_provenance` pre-lock proof, distinguish server-derived
checks from caller-supplied fields without inventing facts, and say that the
proof cannot satisfy the completion gate. Do not choose or implement either
future evidence-authority route.

Output schema:
1. `# Codex Direct Task: medical_monitoring_p8_provenance_disclosure_20260806`
2. `## Boundary Check`
3. `## Direct Work`
4. `## Evidence And Assumptions`
5. `## Verification`
6. `## Residual Risk`
