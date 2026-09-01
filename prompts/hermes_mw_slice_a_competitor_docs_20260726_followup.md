MODE=EXECUTION

Resume the same Slice A execution session. The first pass is evidence, not
acceptance. Address only these two failed checks:

Hard boundaries:
- Work only inside the runner-provided current workspace (`.`).
- Read and modify only the production paths explicitly authorized in
  `context/mw_slice_a_competitor_docs_20260726_context.md`.
- Do not edit `services/api/app/main.py` or any frontend file.
- Tools remain enabled. Do not restart the shared runtime.
- Runner-managed output path:
  `runs/hermes_mw_slice_a_competitor_docs_20260726_followup.md`. Never write
  that report path with tools; return the report and let the runner persist it.

Read these files only:
- `context/mw_slice_a_competitor_docs_20260726_context.md`
- `services/api/app/writing_reference_preparation_batch.py`
- `services/api/app/writing_reference_repository.py`
- `services/api/app/writing_reference.py`
- `services/api/app/main.py`
- `packages/contracts/workbench_contracts/models.py`
- `tests/test_writing_reference_preparation_batch.py`
- `tests/test_writing_reference_repository.py`
- `tests/test_writing_reference_api.py`
- `records/handoffs/codex_retake_20260726/evidence/slice_a_hermes/step4_prep_batch.json`
- `records/handoffs/codex_retake_20260726/evidence/slice_a_hermes/failure_reporting_result.json`

1. `records/handoffs/codex_retake_20260726/evidence/slice_a_hermes/step4_prep_batch.json`
   has `rc=22`, `batch=null`, and no HTTP response detail. Re-run the isolated
   project preparation request without suppressing the HTTP body, identify the
   exact contract failure, and complete one real preparation-batch API path
   using the already discovered ClinicalTrials.gov Protocol/SAP. The raw PDF
   must be persisted in the isolated project's normal runtime artifact store,
   then read back through the repository/API. A direct service call into a
   temporary directory is not sufficient.
2. `failure_reporting_result.json` says `is_explicit=false` and
   `mapped_error_code=ingest_failed`. Reproduce the actual download/network
   failure mapping. If the generic code cannot support a user-facing specific
   explanation, add the smallest deterministic
   `public_document_download_failed` mapping in the authorized preparation
   service plus focused tests. Do not edit frontend code in this pass.

Writable production files remain exactly those listed in the task context.
Do not edit `main.py`, do not confirm or touch the PNH basket, do not create a
placeholder file, and do not use a worker-generated document.

Return the same compact execution schema. In `CHECKS`, include the real HTTP
status/body, batch/item IDs, persisted runtime artifact locator and hash,
repository/API read-back, focused test command/result, and the corrected
failure code. If route wiring outside the writable set is required, stop with
the exact blocker instead of claiming PASS.
