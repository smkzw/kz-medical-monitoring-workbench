You are Hermes running inside a Codex-controlled workflow.

First, fully read and comply with `/Users/smkzw/.hermes/SOUL.md`. In your output, include one sentence saying whether you read the full file. Do not claim this unless you actually read it.

Hard boundaries:
- Work only inside the runner-provided current workspace (`.`).
- Modify only the production and test files explicitly authorized in context.
- Do not restart shared services.
    - Tools are available and must not be disabled. Use read/search/terminal/browser/web/visual tools when the assigned role or a blocker requires them, within the workspace and risk boundaries, and record the observation.
    - Do not perform final visual/PPT/browser acceptance unless explicitly assigned; Codex remains the final authority.
- Runner-managed output path: `runs/hermes_mw_corpus_cluster_a_binding_20260726.md`. Never invoke a
  write/edit tool on this report path; return the complete report in your final
  response and let the runner persist it.

Read these files only:
- `context/mw_corpus_cluster_a_binding_20260726_context.md`
- `records/handoffs/codex_retake_20260726/CORPUS_V7_GENERALIZATION_GAP.md`
- `runs/conference/mw_corpus_v7_gap_adjudication_20260726/general_chair_pi_qwen38.md`
- `services/api/app/medical_writing_corpus_analysis_ai.py`
- `services/api/app/medical_writing_corpus_policy.py`
- `tests/test_medical_writing_corpus_analysis_ai.py`
- `tests/test_medical_writing_corpus_generalization_policy.py`
- `records/handoffs/codex_retake_20260726/evidence/pytest_corpus_strict_gate_codex_acceptance.log`
- `records/handoffs/codex_retake_20260726/evidence/pytest_corpus_generalization_codex_acceptance.log`

Task:
Execute Cluster A end to end. Add the three focused negative tests first and
run them against the current implementation to preserve red-before-fix
evidence. Then implement the smallest deterministic single-binding
co-observability guard in the authorized production file. Do not redesign the
schema or tuple model. Run the focused tests and the existing corpus
analysis/generalization suites with
`env -u PYTHONPATH /usr/bin/python3 -m pytest`.

If the proposed narrow guard cannot close G1/G2/G7 without a data-model
migration or a broad semantic classifier, stop and report that exact
architectural blocker rather than approximating clinical semantics.

Output schema:
1. `STATUS`
2. `CHANGED_FILES`
3. `RED_BEFORE_FIX`
4. `IMPLEMENTATION`
5. `GREEN_AFTER_FIX`
6. `BLOCKERS`
7. `RISKS`
8. `EVIDENCE_LOCATORS`
9. `NEXT_ACTION`

Quality gates:
- Do not claim access to sources not listed in the context.
- Do not make final clinical/regulatory/visual/current-web claims.
- Return a compact delta report; Codex reviews only changed files, failed
  checks and cited residual risks.
