MODE=EXECUTION

Hard boundaries:

- Work only inside the runner-provided current workspace (`.`).
- Modify only the production and test files explicitly authorized in context.
- Do not restart shared services.
- Keep all tools enabled and use them only when required by the bounded task.
- Do not perform final clinical, regulatory, browser or launch acceptance;
  Codex remains final authority.
- Runner-managed output path:
  `runs/hermes_mw_corpus_cluster_a_binding_20260726.md`. Never invoke a
  write/edit tool on this report path; return the complete report in the final
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

Resume the existing Hermes session `20260726_191807_835bf2` for the bounded
Cluster A task in
`context/mw_corpus_cluster_a_binding_20260726_context.md`.

The run was interrupted only because the user requested a no-loss pause.
Preserve and continue the work already present in the session. Do not restart
broad exploration and do not touch files outside the original writable paths.

Current pause evidence:

- `tests/test_medical_writing_corpus_analysis_ai.py` changed during the prior
  pass and may contain the intended red tests.
- `services/api/app/medical_writing_corpus_analysis_ai.py` had not changed at
  the recorded pause boundary.
- No runner-managed report was produced and no partial result was accepted.

Complete the original contract:

1. Confirm the three G1/G2/G7 negative tests are present and preserve a real
   red-before-fix result against the pre-fix production behavior. If the prior
   session already captured that result, cite its exact locator rather than
   recreating it.
2. Implement only the narrow deterministic single-binding/co-observability
   guard authorized by the task context. Do not redesign the tuple schema.
3. Run the focused tests and the pinned existing corpus analysis and
   generalization regressions with
   `env -u PYTHONPATH /usr/bin/python3 -m pytest`.
4. Return a compact delta report with changed files and hashes, red evidence,
   green evidence, failed checks, residual risks and the exact next action.

Codex will inspect only changed files, failed checks and cited risks before
acceptance.
