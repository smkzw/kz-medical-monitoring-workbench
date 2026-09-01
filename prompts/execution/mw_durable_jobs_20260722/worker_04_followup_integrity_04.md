Continue the same `mw_durable_jobs_20260722 / worker_04` session. Fully read
`/Users/smkzw/.hermes/SOUL.md`, workspace `AGENTS.md`, the v3 report and current
source. Preserve all accepted v2/v3 behavior. Do not redo the adapter.

Hard boundaries: write only:

- `services/api/app/writing_reference_translation_batch.py`
- `tests/test_writing_reference_translation_batch.py`
- `tests/test_writing_reference_translation_durable_jobs.py`

Do not edit shared durable core, main.py, frontend, contracts or other adapters.
Do not substitute your model for product AI.

Runner-managed report path:
`runs/execution/mw_durable_jobs_20260722/worker_04_followup_integrity_04.md`.
Return the report in final text and never write that path yourself.

Codex independently reproduced 195 passing tests and confirmed the new v3
guards. Two source-level ownership gaps remain outside those tests:

1. `_run_items()` currently computes item ids and calls `_set_batch_status(...,
   "running")` before its first fail-closed `cancel_check`. A claim can be lost
   after executor entry but before `_run_items`, allowing a stale owner to mutate
   batch status. Perform an exception-safe ownership check before this first
   business write. If lost or the check raises, return without changing batch or
   item state. Add a deterministic test comparing batch/item state and audits.
2. In the existing-integration reuse path, `_guard()` occurs before
   `_link_item_to_chapter_revision()`, but after that potentially writing call the
   code invokes `_finish_composite_item()` without a second guard. Moreover,
   `_finish_composite_item()` and `_exclude_claim_after_document_plan()` call
   `_finish_claim()` without passing `cancel_check`, so the final CAS/audit lacks
   its own ownership proof. Thread `cancel_check` through these helper boundaries,
   recheck after the link and immediately inside the final commit helper. Prove a
   guard flip between link and item completion leaves the item non-terminal and
   emits no completion audit. Apply the same final-commit safety to the normal and
   anchor-exclusion paths.

Also make direct `cancel_check` calls in the touched path exception-safe: an
exception is ownership unknown and must fail closed, never trigger `_fail_claim`
or another business write.

Use deterministic guards/write spies, no timing allowances. Rerun translation
legacy, durable adapter, shared durable core and broader writing-reference tests.
Finish with `WORKER_04_TRANSLATION_INTEGRITY_V4_COMPLETE` only when both missing
boundaries are proven.
