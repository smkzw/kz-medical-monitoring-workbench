You are Hermes running inside a Codex-controlled workflow.

First, fully read and comply with `/Users/smkzw/.hermes/SOUL.md`. In your output, include one sentence saying whether you read the full file. Do not claim this unless you actually read it.

Hard boundaries:
- Work only inside the runner working directory (`.`).
- The workspace is the authorized local product workspace for this bounded
  edit round.
- You may edit only:
  - `frontend/src/features/medical-writing/AuthoringCompetitorDrawer.jsx`
  - `frontend/src/features/writing-reference/WritingReferencePanel.jsx`
  - focused test files under `tests/`.
- Do not edit backend source, r11 evidence, runtime databases, matrix receipts,
  generated `frontend/dist`, or unrelated files.
    - Tools are available and must not be disabled. Use read/search/terminal/browser/web/visual tools when the assigned role or a blocker requires them, within the workspace and risk boundaries, and record the observation.
    - Do not perform final visual/PPT/browser acceptance unless explicitly assigned; Codex remains the final authority.
- Runner-managed output path: `runs/pi_mw_candidate_projection_r11.md`. Never invoke a
  write/edit tool on this report path; return the complete report in your final
  response and let the runner persist it.

Read these files only:
- `context/mw_candidate_projection_r11_context.md`
- `context/mw_final_5x3_release_r11_20260729_context.md`
- `runs/execution/mw_final_5x3_harness_20260728/rounds/release-r11-20260729/slots/A1/lazy_medical_writer/BLOCKED.md`
- `runs/execution/mw_final_5x3_harness_20260728/rounds/release-r11-20260729/slots/A1/lazy_medical_writer/DEFECTS.md`
- `runs/execution/mw_final_5x3_harness_20260728/rounds/release-r11-20260729/slots/A1/lazy_medical_writer/COMPLETION_STATUS.json`
- `runs/execution/mw_final_5x3_harness_20260728/rounds/release-r11-20260729/slots/A1/lazy_medical_writer/screenshots/original_resolution/018_candidate_list_after_confirm.png`
- `runs/execution/mw_final_5x3_harness_20260728/rounds/release-r11-20260729/slots/A1/lazy_medical_writer/service_logs/api.log`
- `frontend/src/features/medical-writing/AuthoringCompetitorDrawer.jsx`
- `frontend/src/features/writing-reference/WritingReferencePanel.jsx`
- `tests/test_frontend_medical_writing_contract.py`
- `tests/test_frontend_medical_writing_pipeline_waiting_contract.py`

Task:
Implement the smallest coherent repair described by the task context.

Required behavior:
- every closed-to-open transition of the persisted competitor drawer must
  trigger a fresh workspace read for the same project and immutable snapshot;
- the request must remain protected against stale project/snapshot responses;
- while the refresh is unresolved, do not render the loaded-empty candidate
  message or a misleading `0项`;
- after a loaded empty snapshot, retain the genuine empty state;
- preserve all triage, confirmation, preparation and corpus semantics.

Add focused deterministic regression coverage that proves the open-transition
refresh signal is wired from `AuthoringCompetitorDrawer` to
`WritingReferencePanel`, and that loaded/refreshing/empty rendering states are
distinguishable. Run the focused tests and `npm run build`.

Before editing, inspect the r11 API log around the final page re-entry and
confirm that latest-triage was requested but the workspace endpoint was not.
Do not guess at backend data loss: the frozen SQLite snapshot has 665
candidates.

Output schema:
1. `# Hermes Execution Result: mw_candidate_projection_r11`
2. `## Boundary Check`
3. `## Root Cause`
4. `## Files Changed`
5. `## Verification`
6. `## Codex Recheck Targets`
7. `## Residual Risk`

Quality gates:
- List exact changed paths and test commands/results.
- Do not claim the separate document-admission blocker is resolved.
- Do not make final clinical/regulatory/visual/current-web claims.
- Keep the patch narrow and compatible with the existing design.
