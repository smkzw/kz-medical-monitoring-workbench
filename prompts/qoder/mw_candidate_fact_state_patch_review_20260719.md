# Qoder Patch Review Assignment

Perform a read-only code review of the newly implemented medical-writing
candidate fact-state provenance patch.

## Read

- `packages/contracts/workbench_contracts/models.py`
- `services/api/app/medical_writing.py`
- `services/api/app/medical_writing_repository.py`
- `tests/test_medical_writing_revision_api.py`
- `tests/test_medical_writing_revision_application.py`
- `tests/test_sqlite_medical_writing_store.py`
- `records/qoder_full_system_audit_20260719/QODER_CANDIDATE_FACT_STATE_AUDIT.md`

The current local evidence is:

- focused tests: 27 passed;
- expanded revision/AI/working-copy suite: 135 passed;
- Ruff: passed.

## Review Questions

1. Does each suggestion derive `evidence_source_types` only from evidence spans
   it actually cites, rather than every source merely provided to the model?
2. Can competitor evidence upgrade a suggestion before explicit medical-author
   `accept`?
3. Does the thread-level union remain correct after a rewrite turn?
4. Do submitted, accepted, and applied audit events retain the required source
   types, adoption state, and adoption basis?
5. Do legacy JSON records remain compatible, including already accepted legacy
   suggestions?
6. Does any code confuse candidate selection with final working-copy approval?
7. Are there any mutation, assignment-validation, idempotency, or persistence
   edge cases introduced by the patch?

## Output Contract

- Do not modify production source or tests.
- Write the complete report to:
  `records/qoder_full_system_audit_20260719/QODER_CANDIDATE_FACT_STATE_PATCH_REVIEW.md`
- Separate P0/P1/P2/P3 findings.
- Include exact file and line references.
- If there is no release blocker, explicitly write `PASS`.
- After writing the file, reply only with its exact path and `DONE`.
