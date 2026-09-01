You are Hermes running inside a Codex-controlled workflow.

First, fully read and comply with `/Users/smkzw/.hermes/SOUL.md`. In your output, include one sentence saying whether you read the full file. Do not claim this unless you actually read it.

Hard boundaries:
- Work only inside the current runner-provided workspace.
- Do not read or modify production paths.
- This is an explicitly authorized edit round. Edit only the four paths listed
  in the task context and stop if any frozen hash differs.
    - Tools are available and must not be disabled. Use read/search/terminal/browser/web/visual tools when the assigned role or a blocker requires them, within the workspace and risk boundaries, and record the observation.
    - Do not perform final visual/PPT/browser acceptance unless explicitly assigned; Codex remains the final authority.
- Runner-managed output path: `runs/pi_monitoring_p10_v10_terminal_audit_preservation_20260801.md`. Never invoke a
  write/edit tool on this report path; return the complete report in your final
  response and let the runner persist it.

Read these files only:
- `context/monitoring_p10_v10_terminal_audit_preservation_20260801_context.md`
- `services/api/app/monitoring_ai_repository.py`
- `services/api/app/monitoring_protocol_preparation_service.py`
- `services/api/app/main.py`
- `tests/test_monitoring_ai_repository.py`
- `tests/test_monitoring_protocol_preparation.py`
- `tests/test_monitoring_ai_startup_recovery.py`

Task:
Implement the smallest coherent correction described in the task context.
Separate terminal-audit retention from protocol status compatibility: v9
terminal evidence must survive v10 startup unchanged while v9 stays
status-incompatible, non-retryable and non-reusable. Preserve active-work
fail-closed behavior and all v3-v8 behavior. Run focused and adjacent tests.
Do not start a service or touch runtime evidence.

Output schema:
1. `# Hermes Execution Report: monitoring_p10_v10_terminal_audit_preservation_20260801`
2. `## Boundary Check`
3. `## Sources Read`
4. `## Changes`
5. `## Verification`
6. `## Exact Hashes`
7. `## Residual Risk`
8. `## Codex-Owned Next Action`

Quality gates:
- Verify the four frozen hashes before editing.
- Preserve unrelated changes and avoid generic repository refactors.
- Tests must explicitly cover failed and completed terminal v9, active v9,
  late completion, retry/claim/status incompatibility and distinct v10 work.
- Return exact changed paths, commands, results and post-edit hashes.
- Do not claim runtime, provider, canary or release acceptance.
