# Qoder Persistence-Boundary Follow-up

Continue the same review session. Codex accepted your correction that
`WorkbenchModel` does not use `validate_assignment`, but found one inaccurate
sentence in the prior follow-up: `model_dump()` does not itself rerun the model
validator.

Codex therefore added a bounded persistence-boundary hardening change:

- `services/api/app/sqlite_runtime_store.py`
  - `commit_medical_writing_revision_action` now reconstructs both
    `previous_thread` and `updated_thread` through
    `RevisionThread.model_validate(model_dump(mode="json"))` before building
    the request payload or writing.
- `tests/test_sqlite_medical_writing_store.py`
  - added
    `test_action_persistence_revalidates_in_memory_candidate_adoption_state`.

Read the latest source and test. Verify:

1. Invalid direct in-memory assignment cannot be committed.
2. The hardening does not break legacy normalization, optimistic concurrency,
   idempotency, or valid accept/reject/rewrite paths.
3. The new test proves the persistence-boundary invariant and stored state is
   unchanged on rejection.

Do not modify source or tests. Append a short final addendum to
`records/qoder_full_system_audit_20260719/QODER_CANDIDATE_FACT_STATE_PATCH_REVIEW.md`.
State P0-P3 and whether PASS remains valid. Reply only with the report path and
`DONE`.
