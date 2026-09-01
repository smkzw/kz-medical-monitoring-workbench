Continue the same bounded `aishuo/MiniMax-M3` sub-venue review session. Continue complying with `/Users/smkzw/.hermes/SOUL.md`; state honestly that it was read in the original session. Codex independently confirmed F-1/F-3 and F-2, then patched them.

Hard boundaries:
- No edits, tests, web, browser, images, original clinical folders or production writes.
- Read only the files listed below.
- Write exactly one output file: `runs/conference/eligibility_unit_ledger_v14_gate_20260712/aishuo_followup.md`.

Read these files only:

- `services/api/app/eligibility_review_workflow.py`
- `services/api/app/eligibility_raw_intake.py`
- `services/api/app/eligibility.py`
- `services/api/app/sqlite_runtime_store.py`
- `tests/test_eligibility_review_workflow.py`
- `tests/test_eligibility_six_subject_matrix.py`
- `records/active_slices/eligibility_next_slice_20260711/six_subject_matrix_v2.json`

Verify from current source whether:

1. canonical subject-source revision now binds unit kind, expected count and count status, and rejects a mismatched supplied revision;
2. raw intake and product mapping use the same canonical function;
3. aggregate subject review now obtains current source revision from durable SQLite rather than process-local memory;
4. the six-subject strict AI gate remains fail-closed.

State whether F-1/F-3 and F-2 are closed. Reclassify F-4 explicitly as either a bounded legacy-compatibility concern or a current P1, with a concrete current public-path reproducer if you claim P1. List any new evidence-backed P0/P1 only. Codex retains final authority.
