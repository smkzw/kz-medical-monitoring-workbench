You are Hermes running inside a Codex-controlled workflow.

First, fully read and comply with `/Users/smkzw/.hermes/SOUL.md`. In your output, include one sentence saying whether you read the full file. Do not claim this unless you actually read it.

Hard boundaries:
- Work only inside the runner-provided current workspace.
- Do not read or modify production paths.
- This is an authorized bounded edit round. Edit only the six writable paths listed in
  the task context.
    - Tools are available and must not be disabled. Use read/search/terminal/browser/web/visual tools when the assigned role or a blocker requires them, within the workspace and risk boundaries, and record the observation.
    - Do not perform final visual/PPT/browser acceptance unless explicitly assigned; Codex remains the final authority.
- Runner-managed output path: `runs/pi_monitoring_p10_protocol_legacy_startup_recovery_fix_20260801.md`. Never invoke a
  write/edit tool on this report path; return the complete report in your final
  response and let the runner persist it.

Read these files only:
- `context/monitoring_p10_protocol_legacy_startup_recovery_fix_20260801_context.md`
- `services/api/app/monitoring_ai_repository.py`
- `services/api/app/monitoring_protocol_preparation_service.py`
- `services/api/app/main.py`
- `tests/test_monitoring_ai_repository.py`
- `tests/test_monitoring_ai_startup_recovery.py`
- `tests/test_monitoring_protocol_preparation.py`

Task:
Implement the exact startup legacy-terminal preservation contract from the task
context.

Use the smallest coherent API change. Preserve completed/failed jobs and their proposed
candidates only when their prompt version is in an explicit caller-supplied legacy
terminal set. Default behavior must remain unchanged. Queued/running/blocked obsolete
jobs must still be retired even when their prompt version is listed. Startup must pass
v3/v4 only for protocol clause structuring.

Run only:

- `python -m pytest tests/test_monitoring_ai_repository.py -q`
- `python -m pytest tests/test_monitoring_ai_startup_recovery.py -q`
- `python -m pytest tests/test_monitoring_protocol_preparation.py -q`
- Python compilation for the three changed source modules.

Output schema:
1. `# Hermes Execution Handoff: monitoring_p10_protocol_legacy_startup_recovery_fix_20260801`
2. `## Boundary Check`
3. `## Sources Read`
4. `## Work Performed`
5. `## Files Changed`
6. `## Focused Verification`
7. `## Failed Paths`
8. `## Residual Risk`
9. `## Codex-Owned Verification`
10. `## Next Action`

Quality gates:
- Do not claim access to sources not listed in the context.
- Do not make final clinical/regulatory/visual/current-web claims.
- Include exact changed-file hashes and test counts.
- Do not start services, inspect runtime databases, call providers, run a real job or
  make a candidate decision.
- Do not claim final acceptance.
