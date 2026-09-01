MODE=EXECUTION

Hard boundaries:

- Work only inside the runner-provided current workspace (`.`).
- Modify only:
  - `tests/test_medical_writing_corpus_analysis_ai.py`;
  - `services/api/app/medical_writing_corpus_analysis_ai.py` only if the
    strengthened tests reveal a real production defect.
- Do not restart shared services or touch policy, runtime, browser, OCR,
  translation or unrelated corpus files.
- Runner-managed output path:
  `runs/hermes_mw_corpus_cluster_a_binding_20260726_followup.md`. Never write
  this report path directly; return the full compact report for the runner.

Read these files only:

- `context/mw_corpus_cluster_a_binding_20260726_context.md`
- `runs/hermes_mw_corpus_cluster_a_binding_20260726.md`
- `services/api/app/medical_writing_corpus_analysis_ai.py`
- `tests/test_medical_writing_corpus_analysis_ai.py`
- `tests/test_medical_writing_corpus_generalization_policy.py`

Resume Hermes session `20260726_191807_835bf2`.

Codex rejected final acceptance for one precise reason: the report states the
G2 and G7 tests passed before the fix because sanitization incidentally removed
their facts. They therefore do not prove that the new single-binding guard
closes G2/G7.

Strengthen only G2 and G7:

1. Build fixtures where every claimed nonnumeric layer value is individually
   present in at least one bound source, so sanitization retains all values,
   but no single binding contains the full route/modality or
   phase/route/modality combination.
2. In each test, include a deterministic counterfactual using `monkeypatch`
   to bypass `_single_binding_substantiates` and prove the old path reaches
   high confidence. Then run the real guard and prove it downgrades to
   `requires_medical_review` with
   `single_binding_co_observability_not_met`.
3. Keep G1 intact. Do not broaden the production implementation unless these
   fixtures expose a defect.
4. Run the three focused tests, the full analysis-AI suite, the
   generalization-policy suite and the same broad corpus selection cited in
   the prior report.

Return only:
STATUS, CHANGED_FILES, COUNTERFACTUAL_PRE_FIX, GREEN_WITH_GUARD, REGRESSIONS,
FAILED_CHECKS, RISKS, EVIDENCE_LOCATORS, NEXT_ACTION.

