Continue the same `mw_durable_jobs_20260722 / worker_04` session. Fully reread and comply with `/Users/smkzw/.hermes/SOUL.md` and workspace `AGENTS.md`.

The prior runner was interrupted after code and a new test file were partially written. Do not restart from scratch and do not overwrite current work. First read the current files, reconcile them with your original assignment, then finish only the missing implementation/tests/report.

Hard boundaries:
- Work only inside the runner-provided current workspace (`.`).
- Sole write ownership remains `services/api/app/writing_reference_translation_batch.py`, `tests/test_writing_reference_translation_batch.py`, and `tests/test_writing_reference_translation_durable_jobs.py`.
- Do not edit `main.py`, frontend, shared durable core, contracts/models, OCR/Hy-MT2/Flash pipeline implementations, corpus admission, or unrelated services.
- Runner-managed report path: `runs/execution/mw_durable_jobs_20260722/worker_04_followup_complete_01.md`. Never write/edit that path; return the complete report in final text.
- Do not substitute execution-model output for the product OCR/translation/QC models.

Read initially:
- `AGENTS.md`
- original prompt `prompts/execution/mw_durable_jobs_20260722/worker_04.md`
- `services/api/app/medical_writing_durable_jobs.py`
- current `services/api/app/writing_reference_translation_batch.py`
- current `tests/test_writing_reference_translation_batch.py`
- current `tests/test_writing_reference_translation_durable_jobs.py`

Acceptance requirements:
1. Create/retry returns without translating on caller thread and creates/reuses one `reference_translation` durable job with stable identity.
2. A fresh service/worker process using only SQLite-persisted input can recover pending batches; an unexpired live owner is not stolen, while an expired lease can be taken over.
3. Completed items/chunks and immutable document-plan work are reused, never retranslated. Failed-retryable work resumes only the failed set.
4. Cancellation and claim loss are checked before and after expensive item/chunk work and before every business write; stale/old owner cannot write item or terminal state. Progress is monotonic and project-isolated.
5. Existing GLM-OCR-bf16 8-way and >200-DPI figure/table requirement, Flash section planning/integration/QC, Hy-MT2 translation, fidelity review and corpus-admission boundaries remain unchanged.
6. Deterministic tests cover pending restart, unexpired lease no-takeover, expired takeover, completed reuse, retry, cancel, old-owner isolation and project isolation. Run the focused translation legacy + durable tests and shared durable core.

Return a complete auditable report. Finish with `WORKER_04_TRANSLATION_DURABLE_COMPLETE` only if all requirements are proven; otherwise state the exact resume point without the marker.
