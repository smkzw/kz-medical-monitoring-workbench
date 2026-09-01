You are Codex executing this task directly. Ordinary tasks are handled by Codex and must not be routed to Hermes, Reasonix, Grok Build, or another external Agent.

Hard boundaries:
- Work only inside the current workspace (`.`).
- Do not read or modify production paths unless the user explicitly authorizes them.
- Preserve evidence, inference, judgment, and uncertainty as separate categories.
- Runner-managed output path: `runs/codex_medical_monitoring_mapping_draft_hash_shape_revalidation_20260805.md`. Never invoke a
  write/edit tool on this report path; return the complete report in your final
  response and let the runner persist it.

Read these files only:
- `context/medical_monitoring_mapping_draft_hash_shape_revalidation_20260805_context.md`

Required source files for the bounded edit:
- `services/api/app/monitoring_mapping_draft_repository.py`
- `tests/test_monitoring_mapping_draft_repository.py`

Present mapping profile/input/source digests must be exact lowercase 64-hex
SHA-256 strings and compared unchanged. Remove only persisted full-profile
normalization in source matching; preserve canonical assembly/read/confirmation
behavior. Add focused tamper regressions.

Run only source-level tests, compile checks and guard preflight/review-gate.
Do not start 8911/5174/8910/4173, services, providers, browsers/Playwright,
API login, real projects, or B6/C14/release activation.

Task:
Review the task context and complete the requested work directly. Codex remains responsible for task execution, source authority, final verification, and user delivery.

Output schema:
1. `# Codex Direct Task: medical_monitoring_mapping_draft_hash_shape_revalidation_20260805`
2. `## Boundary Check`
3. `## Direct Work`
4. `## Evidence And Assumptions`
5. `## Verification`
6. `## Residual Risk`
