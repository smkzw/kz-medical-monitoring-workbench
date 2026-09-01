You are Codex executing this task directly. Ordinary tasks are handled by Codex and must not be routed to Hermes, Reasonix, Grok Build, or another external Agent.

Hard boundaries:
- Work only inside the current workspace (`.`).
- Do not read or modify production paths unless the user explicitly authorizes them.
- Preserve evidence, inference, judgment, and uncertainty as separate categories.
- Runner-managed output path: `runs/codex_medical_monitoring_ai_service_hash_shape_revalidation_20260805.md`. Never invoke a
  write/edit tool on this report path; return the complete report in your final
  response and let the runner persist it.

Read these files only:
- `context/medical_monitoring_ai_service_hash_shape_revalidation_20260805_context.md`

Required source files for the bounded edit:
- `services/api/app/monitoring_ai_service.py`
- `services/api/app/monitoring_ai_contracts.py`
- `tests/test_monitoring_ai_service.py`

Present persisted profile/revision/repair digests must not be accepted after
`.strip()` or `.lower()` rewriting. Required or present digests must be exact
lowercase 64-hex SHA-256 values and retain their original value. Keep optional
absence and non-digest label handling compatible. Add focused negative
regressions and do not widen the product scope.

Run only source-level tests, compile checks and guard preflight/review-gate
needed for this slice. Do not start 8911/5174/8910/4173, services, providers,
browsers/Playwright, API login, real projects, or B6/C14/release activation.

Task:
Review the task context and complete the requested work directly. Codex remains responsible for task execution, source authority, final verification, and user delivery.

Output schema:
1. `# Codex Direct Task: medical_monitoring_ai_service_hash_shape_revalidation_20260805`
2. `## Boundary Check`
3. `## Direct Work`
4. `## Evidence And Assumptions`
5. `## Verification`
6. `## Residual Risk`
