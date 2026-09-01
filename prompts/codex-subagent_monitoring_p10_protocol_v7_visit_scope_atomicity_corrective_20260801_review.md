You are a Codex native subAgent performing an independent read-only acceptance
review under a parent Codex task. Reuse this existing session; do not dispatch any
other agent or external model.

Hard boundaries:
- Work only in the current workbench (`.`).
- Do not modify any file/database/service/API/candidate/runtime state.
- Do not start 8911/5174, run real projects, retry v6, call a provider, salvage
  prose, or make candidate decisions.
- Parent Codex owns final clinical/runtime/release acceptance.
- Runner-managed output path:
  `runs/codex-subagent_monitoring_p10_protocol_v7_visit_scope_atomicity_corrective_20260801_review.md`.
  Do not write it with tools; return the complete handoff to the parent.

Read these files only:
- `context/monitoring_p10_protocol_v7_visit_scope_atomicity_corrective_20260801_context.md`
- `runs/codex-subagent_monitoring_p10_loop316_protocol_v6_visit_canary_20260801.md`
- `runs/pi_monitoring_p10_protocol_v7_visit_scope_atomicity_corrective_20260801.md`
- `services/api/app/monitoring_ai_service.py`
- `services/api/app/monitoring_protocol_preparation_service.py`
- `tests/test_monitoring_ai_service.py`
- `tests/test_monitoring_protocol_preparation.py`
- `tests/test_monitoring_ai_api.py`

Task:
Perform an independent contradiction-oriented code and test review of the complete
v7 offline corrective.

Required review:
1. Confirm prompt v7 and terminal legacy v3-v6 semantics do not permit active v6
   reuse/retry.
2. Reconstruct the visit validation order and prove that full user-visible
   topic-boundary text is separate from operative-only family classification.
3. Challenge medication/first-dose, withdrawal and distributed AE/CM regexes for
   material false negatives and false positives, especially timing-only language.
4. Audit the candidate-indexed aggregation for prerequisite blocking, absence of
   cascading errors, stable order, whole-response atomicity and no regression to
   non-protocol task behavior.
5. Check that structural repair, evidence materialization, claim anchors, conflicts,
   50-ID cap, language and forbidden-assertion gates remain fail-closed.
6. Map the reviewer-required negative matrix to actual tests; identify missing
   decisive cases, test bugs or assertions that do not prove their stated behavior.
7. Consider the Pi boundary deviation: its initial pass read three supporting files
   beyond the explicit read-only list. State whether this affected product changes
   or acceptance evidence; do not excuse or overstate it.
8. Give a clear offline verdict: pass, revise, or reject; state whether one fresh
   RUX v7 visit canary is now the next safe action. MY009 remains blocked.

Parent Codex verification already observed:
- focused v7/direct three-file suite: 276 passed;
- full `pytest tests -q -k monitoring`: 1271 passed / 4299 deselected /
  27 warnings / 0 failed;
- five-file medical-writing adjacent suite: 200 passed / 0 failed;
- `py_compile` passed; 8911/5174 stopped.
Treat these as parent-observed evidence, not your own tool result.

Output schema:
1. `# Codex Independent Review: monitoring_p10_protocol_v7_visit_scope_atomicity_corrective_20260801`
2. `## Boundary Check`
3. `## Contract And Validator Reconstruction`
4. `## Regex And Field-View Challenge`
5. `## Candidate-Indexed Aggregation Audit`
6. `## Negative-Test Matrix Audit`
7. `## Boundary Deviation Assessment`
8. `## Findings`
9. `## Verdict And Next Gate`
