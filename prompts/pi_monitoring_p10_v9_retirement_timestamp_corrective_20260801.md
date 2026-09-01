You are Hermes running inside a Codex-controlled workflow.

First, fully read and comply with `/Users/smkzw/.hermes/SOUL.md`. In your output, include one sentence saying whether you read the full file. Do not claim this unless you actually read it.

Hard boundaries:
- Work only inside the current workbench workspace.
- Do not read or modify production paths.
- This is an authorized bounded edit round. Edit only:
  - `services/api/app/monitoring_ai_repository.py`
  - `tests/test_monitoring_ai_repository.py`
  - `tests/test_monitoring_protocol_preparation.py`
    - Tools are available and must not be disabled. Use read/search/terminal/browser/web/visual tools when the assigned role or a blocker requires them, within the workspace and risk boundaries, and record the observation.
    - Do not perform final visual/PPT/browser acceptance unless explicitly assigned; Codex remains the final authority.
- Runner-managed output path: `runs/pi_monitoring_p10_v9_retirement_timestamp_corrective_20260801.md`. Never invoke a
  write/edit tool on this report path; return the complete report in your final
  response and let the runner persist it.

Read these files only:
- `context/monitoring_p10_v9_retirement_timestamp_corrective_20260801_context.md`
- `runs/execution/monitoring_p10_v9_isolated_canary_20260801/ATTEMPT1_ZERO_SUBMIT_GATE.md`
- `services/api/app/monitoring_ai_repository.py`
- `tests/test_monitoring_ai_repository.py`
- `tests/test_monitoring_protocol_preparation.py`

Task:
Implement the timestamp-preservation corrective described in the context.

Required behavior:

1. The marker-only update in `_apply_contract_supersession()` must not change
   `updated_at`.
2. Rows actually transitioned to `stale_input` must still set `updated_at` to
   the retirement time.
3. Add direct assertions for already-stale marker-only retirement, preserved
   completed/failed legacy prompt retirement, and active queued/running
   retirement timestamp advancement.
4. Preserve every other contract, including first-marker immutability,
   candidates, failure evidence, retry refusal and input-only compatibility.
5. Run focused tests for the changed repository/protocol surfaces. Do not start
   services or touch runtime.

Before editing, verify all three frozen hashes from the context. If any differs,
stop without editing and report the mismatch.

Output schema:
1. `# Hermes Execution Report: monitoring_p10_v9_retirement_timestamp_corrective_20260801`
2. `## Boundary Check`
3. `## Changes`
4. `## Tests And Evidence`
5. `## Residual Risk`
6. `## Codex-Owned Next Verification`

Quality gates:
- Do not claim access to sources not listed in the context.
- Do not make final clinical/regulatory/visual/current-web claims.
- Report exact changed paths, final SHA-256 values and full test counts.
- Do not claim canary/runtime/release acceptance.
