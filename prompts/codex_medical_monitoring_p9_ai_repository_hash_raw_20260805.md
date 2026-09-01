You are Codex executing this task directly. Ordinary tasks are handled by Codex and must not be routed to Hermes, Reasonix, Grok Build, or another external Agent.

Hard boundaries:
- Work only inside the current workbench workspace.
- Do not read or modify production paths unless the user explicitly authorizes them.
- Preserve evidence, inference, judgment, and uncertainty as separate categories.
- Runner-managed output path: `runs/codex_medical_monitoring_p9_ai_repository_hash_raw_20260805.md`. Never invoke a
  write/edit tool on this report path; return the complete report in your final
  response and let the runner persist it.

Read these files only:
- `context/medical_monitoring_p9_ai_repository_hash_raw_20260805_context.md`

Task:
Review the task context and complete the requested work directly. Codex remains responsible for task execution, source authority, final verification, and user delivery.

Bounded objective: make the monitoring AI repository's persisted digest validator require exact raw lowercase 64-hex strings without `str(...).strip()` normalization. Add focused persisted-row regressions and run source-only tests/compilation. Do not activate any provider, runtime, service, browser, API login, or real project.

Output schema:
1. `# Codex Direct Task: medical_monitoring_p9_ai_repository_hash_raw_20260805`
2. `## Boundary Check`
3. `## Direct Work`
4. `## Evidence And Assumptions`
5. `## Verification`
6. `## Residual Risk`
