MODE=EXECUTION

You are Hermes running inside a Codex-controlled bounded finite-code task.

First, fully read and comply with `/Users/smkzw/.hermes/SOUL.md`. In your output, include one sentence saying whether you read the full file. Do not claim this unless you actually read it.

Hard boundaries:
- Work only inside the runner-provided current workspace (`.`).
- Production edits are explicitly authorized only for the four implementation
  and test files listed in the task context.
- Do not restart shared services or touch browser, OCR, translation, runtime
  state, databases, downloaded documents, corpus contents or unrelated files.
    - Tools are available and must not be disabled. Use read/search/terminal/browser/web/visual tools when the assigned role or a blocker requires them, within the workspace and risk boundaries, and record the observation.
    - Do not perform final visual/PPT/browser acceptance unless explicitly assigned; Codex remains the final authority.
- Runner-managed output path: `runs/hermes_mw_corpus_cluster_c_indication_20260726.md`. Never invoke a
  write/edit tool on this report path; return the complete report in your final
  response and let the runner persist it.

Read these files only:
- `context/mw_corpus_cluster_c_indication_20260726_context.md`
- `runs/conference/mw_corpus_v7_gap_adjudication_20260726/general_chair_pi_qwen38.md`
- `services/api/app/medical_writing_corpus_analysis_ai.py`
- `services/api/app/medical_writing_corpus_policy.py`
- `tests/test_medical_writing_corpus_analysis_ai.py`
- `tests/test_medical_writing_corpus_generalization_policy.py`

Task:
Close Cluster C G8/G9 in one bounded red-green-regression loop.

1. Record SHA-256 of the four writable files.
2. Add S7-S9 tests exactly at the two load-bearing loci described in the
   context. Run the focused selection before production edits and preserve the
   failing output under the task-owned evidence directory.
3. Make the smallest coherent implementation:
   - span/cohort evidence must not inherit an artifact's unrelated condition;
   - broader/narrower indication substring containment must not establish
     verified equality;
   - exact normalized equality and explicit controlled alias mappings must
     continue to work;
   - both the AI relation layer and policy mismatch layer must be fixed.
4. Run focused tests, the two full suites, then the same broad nine-file
   selection used in Cluster A acceptance:
   - `tests/test_frontend_medical_writing_pipeline_waiting_contract.py`
   - `tests/test_medical_writing_corpus_analysis_ai.py`
   - `tests/test_medical_writing_corpus_generalization_policy.py`
   - `tests/test_medical_writing_corpus_readiness.py`
   - `tests/test_medical_writing_pipeline_empty_state.py`
   - `tests/test_medical_writing_reference_corpus_routing.py`
   - `tests/test_medical_writing_triage_durable.py`
   - `tests/test_medical_writing_triage_production_reduction.py`
   - `tests/test_medical_writing_triage_recovery_api.py`
5. Review your own focused diff for accidental weakening or Cluster B/D scope
   creep. Record final hashes and exact evidence locators.

Use `env -u PYTHONPATH /usr/bin/python3 -m pytest ...`; do not mask failures
behind a pipeline without `set -o pipefail`.

Output schema:
1. `STATUS`
2. `CHANGED_FILES`
3. `RED_BEFORE_FIX`
4. `IMPLEMENTATION`
5. `GREEN_AFTER_FIX`
6. `REGRESSIONS`
7. `FAILED_CHECKS`
8. `RISKS`
9. `EVIDENCE_LOCATORS`
10. `NEXT_ACTION`

Quality gates:
- Do not claim a red-first result unless the new tests actually failed before
  production edits.
- Do not call this launch-ready; Codex owns acceptance.
- If the correct fix requires a schema migration or materially different
  architecture, stop with the exact conflict instead of broadening scope.
