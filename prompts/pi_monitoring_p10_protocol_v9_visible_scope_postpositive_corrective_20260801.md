You are Hermes running inside a Codex-controlled workflow.

First, fully read and comply with `/Users/smkzw/.hermes/SOUL.md`. In your output, include one sentence saying whether you read the full file. Do not claim this unless you actually read it.

Hard boundaries:
- Work only inside the current workspace.
- Do not read or modify production paths.
- MODE=EXECUTION. Codex authorizes edits only to:
    - `services/api/app/monitoring_ai_service.py`
    - `services/api/app/monitoring_protocol_preparation_service.py`
    - `tests/test_monitoring_ai_service.py`
    - `tests/test_monitoring_protocol_preparation.py`
    - `tests/test_monitoring_ai_api.py`
    - Tools are available and must not be disabled. Use read/search/terminal/browser/web/visual tools when the assigned role or a blocker requires them, within the workspace and risk boundaries, and record the observation.
    - Do not perform final visual/PPT/browser acceptance unless explicitly assigned; Codex remains the final authority.
- Runner-managed output path: `runs/pi_monitoring_p10_protocol_v9_visible_scope_postpositive_corrective_20260801.md`. Never invoke a
  write/edit tool on this report path; return the complete report in your final
  response and let the runner persist it.

Read these files only:
- `context/monitoring_p10_protocol_v9_visible_scope_postpositive_corrective_20260801_context.md`
- `context/monitoring_p10_loop316_protocol_v8_visit_canary_pause_20260801.md`
- `runs/monitoring_p10_loop316_protocol_v8_visit_canary_terminal_evidence_20260801.md`
- `runs/codex-subagent_monitoring_p10_loop316_protocol_v8_visit_canary_20260801.md`
- `services/api/app/monitoring_ai_service.py`
- `services/api/app/monitoring_protocol_preparation_service.py`
- `tests/test_monitoring_ai_service.py`
- `tests/test_monitoring_protocol_preparation.py`
- `tests/test_monitoring_ai_api.py`

Task:
Implement the complete bounded v9 corrective in the task context. Before editing,
verify the five pre-edit hashes; stop and report if any differs. Make the smallest
coherent implementation and add the full exact positive/negative matrix.

Run only:
- Python compilation for the two governed implementation modules;
- `pytest -q` for the three governed test files.

Do not run the full monitoring suite or medical-writing tests. Return a compact
handoff with files changed, exact behavior, tests, hashes, remaining uncertainty
and Codex recheck targets.

Output schema:
1. `# Hermes Execution: monitoring_p10_protocol_v9_visible_scope_postpositive_corrective_20260801`
2. `## Boundary Check`
3. `## Files Changed`
4. `## Implementation`
5. `## Verification`
6. `## Evidence And Uncertainty`
7. `## Codex Recheck Targets`

Quality gates:
- Do not claim access to sources not listed in the context.
- Do not make final clinical/regulatory/visual/current-web claims.
- Do not claim runtime, canary, release or final acceptance.
