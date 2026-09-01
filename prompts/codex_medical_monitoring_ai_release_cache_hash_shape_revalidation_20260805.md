You are Codex executing this task directly. Ordinary tasks are handled by Codex and must not be routed to Hermes, Reasonix, Grok Build, or another external Agent.

Hard boundaries:
- Work only inside the current workspace (`.`).
- Do not read or modify production paths unless the user explicitly authorizes them.
- Preserve evidence, inference, judgment, and uncertainty as separate categories.
- Runner-managed output path: `runs/codex_medical_monitoring_ai_release_cache_hash_shape_revalidation_20260805.md`. Never invoke a
  write/edit tool on this report path; return the complete report in your final
  response and let the runner persist it.

Read these files only:
- `context/medical_monitoring_ai_release_cache_hash_shape_revalidation_20260805_context.md`
- `services/api/app/monitoring_ai_release.py`
- `services/api/app/monitoring_ai_release_gate.py`
- `services/api/app/monitoring_ai_field_profile_cache.py`
- `tests/test_monitoring_ai_release.py`
- `tests/test_monitoring_ai_release_gate.py`
- `tests/test_monitoring_ai_field_profiler.py`

The authoritative runtime gate is read-only and blocked. Do not start services,
providers, browsers, Playwright, API logins or real projects. Preserve release
approval/activation semantics and optional empty fields; only fix justified
present-digest shape normalization with `apply_patch` inside the workspace.

Task:
Review the task context and complete the requested work directly. Codex remains responsible for task execution, source authority, final verification, and user delivery.

Output schema:
1. `# Codex Direct Task: medical_monitoring_ai_release_cache_hash_shape_revalidation_20260805`
2. `## Boundary Check`
3. `## Direct Work`
4. `## Evidence And Assumptions`
5. `## Verification`
6. `## Residual Risk`
