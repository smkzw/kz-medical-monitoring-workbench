# Qoder Targeted Follow-up

Continue the same review session. The previous report passed the patch, but two
items require focused verification after the report was written.

## Additional Source

Read:

- `services/api/app/sqlite_runtime_store.py`, especially
  `commit_medical_writing_revision_action`
- the latest
  `tests/test_sqlite_medical_writing_store.py`

## Questions

1. A legacy SQLite row lacks the additive fields. On read, Pydantic supplies
   defaults; optimistic concurrency then compares the previous-thread hash with
   the stored row. Verify that normalizing the stored JSON through
   `RevisionThread.model_validate(...).model_dump(...)` before hashing prevents
   false stale-write rejection without hiding real semantic concurrent writes.
2. `WorkbenchModel` does not set `validate_assignment=True`. Correct the prior
   report's assignment-validation claim. Determine whether current service-only
   mutation paths remain safe and whether a release-blocking change is needed.
3. Review the new legacy cold-restart action test for whether it actually
   reproduces the old false-stale condition.

## Output

- Do not modify source or tests.
- Append a clearly titled follow-up section to
  `records/qoder_full_system_audit_20260719/QODER_CANDIDATE_FACT_STATE_PATCH_REVIEW.md`.
- State P0-P3 and whether the prior PASS remains valid.
- Reply only with the report path and `DONE`.
