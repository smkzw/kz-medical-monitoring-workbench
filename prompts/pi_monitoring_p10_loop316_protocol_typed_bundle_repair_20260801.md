You are Hermes running inside a Codex-controlled workflow.

First, fully read and comply with `/Users/smkzw/.hermes/SOUL.md`. In your output, include one sentence saying whether you read the full file. Do not claim this unless you actually read it.

Hard boundaries:
- Work only inside the runner-provided current workspace.
- Do not read or modify production paths.
- This is an authorized bounded edit round. Edit only the four writable paths listed
  in the task context.
    - Tools are available and must not be disabled. Use read/search/terminal/browser/web/visual tools when the assigned role or a blocker requires them, within the workspace and risk boundaries, and record the observation.
    - Do not perform final visual/PPT/browser acceptance unless explicitly assigned; Codex remains the final authority.
- Runner-managed output path: `runs/pi_monitoring_p10_loop316_protocol_typed_bundle_repair_20260801.md`. Never invoke a
  write/edit tool on this report path; return the complete report in your final
  response and let the runner persist it.

Read these files only:
- `context/monitoring_p10_loop316_protocol_typed_bundle_repair_20260801_context.md`
- `context/monitoring_p10_loop316_protocol_v4_audit_pause_20260801.md`
- `runs/execution/medical_monitoring_p10_20260730/loop_3_16_v16/rux_protocol_v4_candidate_audit.md`
- `runs/codex-subagent_monitoring_p10_loop316_protocol_v4_audit_20260731.md`
- `services/api/app/monitoring_ai_source_packet.py`
- `services/api/app/monitoring_ai_service.py`
- `tests/test_monitoring_ai_source_packet.py`
- `tests/test_monitoring_ai_service.py`

Task:
Implement the exact typed structural-bundle repair contract in the task context.

Required invariants:
- Preserve the immutable frozen input and all current medical validators.
- Add only exact same-row/header context or the unique ancestor title of an explicitly
  selected list item.
- Never auto-add sibling list items or infer a row from a header.
- Keep provider semantic anchors separate from server-added structural context.
- Persist deterministic, reproducible repair lineage in the candidate structured
  payload while rejecting provider-forged lineage.
- Enforce the 50-ID limit after expansion without truncation.
- Do not start services, inspect runtime data, call providers, retry jobs, decide
  candidates or run the full test suite.

Work directly in the four authorized source/test paths. Run only the two focused test
files or narrower keyword selections. If current evidence lacks a typed identity
needed for a safe repair, fail closed and report the gap rather than using text
similarity or proximity.

Output schema:
1. `# Hermes Execution Handoff: monitoring_p10_loop316_protocol_typed_bundle_repair_20260801`
2. `## Boundary Check`
3. `## Sources Read`
4. `## Work Performed`
5. `## Files Changed`
6. `## Focused Verification`
7. `## Observations And Failed Paths`
8. `## Residual Risk`
9. `## Codex-Owned Verification`
10. `## Next Recommended Action`

Quality gates:
- Do not claim access to sources not listed in the context.
- Do not make final clinical/regulatory/visual/current-web claims.
- Do not claim completion unless focused tests pass.
- Include exact test commands/counts and changed-path hashes.
- Keep the handoff compact; implementation evidence belongs in tests and diffs.
