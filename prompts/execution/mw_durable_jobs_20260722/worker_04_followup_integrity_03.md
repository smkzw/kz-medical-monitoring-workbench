Continue the same `mw_durable_jobs_20260722 / worker_04` session. Reread
`/Users/smkzw/.hermes/SOUL.md`, workspace `AGENTS.md`, the v2 report and current
source. Preserve accepted fixes. Do not redo the adapter.

Hard boundaries: write only:

- `services/api/app/writing_reference_translation_batch.py`
- `tests/test_writing_reference_translation_batch.py`
- `tests/test_writing_reference_translation_durable_jobs.py`

Do not edit shared durable core, main.py, frontend, contracts, OCR/Hy-MT2/Flash
implementations, corpus admission, triage or revision services. Do not
substitute your model for product AI.

Runner-managed report path:
`runs/execution/mw_durable_jobs_20260722/worker_04_followup_integrity_03.md`.
Return it in final text; never write that path yourself.

Codex independently reproduced 127 passing focused tests. However, source review
shows that v2 did not close the explicit old-owner business-write contract.
`_process_with_composite_pipeline()` still writes before checking ownership:

- document plan creation and `_persist_pipeline_stage()` progress writes;
- `repository.save_translation_chunk()`;
- `repository.save_chapter_integration_result()` around current line 1995;
- `repository.save_composite_pipeline_run()` around current line 2024;
- `repository.save_translation()` around current line 2072;
- reuse-path `_link_item_to_chapter_revision()` before the later item finish.

The current cancel check at about line 2078 is too late: a stale owner has already
persisted the final translation revision. The prior acceptance contract expressly
required that after claim loss during slow product AI there be no translation
revision, chapter integration, item terminal state or completion audit from the
old owner. The report claimed this was fixed, but the source disproves it.

Close the gap with the smallest coherent design:

1. Thread a fail-closed ownership guard through every persistence boundary in
   the actual composite and reuse paths. Check immediately after each expensive
   product-AI call and immediately before every repository/business commit.
   Include document-plan creation, stage progress, chunks, integration, composite
   run, translation revision, item completion/failure and audit writes.
2. If ownership is lost or checking ownership raises, stop without any later
   business write. Never treat an ownership-check exception as success.
3. At executor entry, check ownership before
   `recover_interrupted_items_for_batch`; a stale/cancelled executor invocation
   must not recover or mutate a running item.
4. Add deterministic adapter-level fault tests with a guard that flips at each
   named boundary. At minimum prove loss after Hy-MT2/chunk generation, after
   Flash integration but before integration save, before final translation save,
   and in the reuse path. Compare repository rows/audits before and after; do not
   use timing allowances.
5. Preserve immutable successful work only when it was committed while ownership
   was positively proven. Do not delete previously valid artifacts.
6. Preserve v2 live-owner recovery, false-heartbeat, false-success, retry-order
   and startup recovery behavior.

Rerun translation legacy, durable adapter and shared durable-core tests. Finish
with `WORKER_04_TRANSLATION_INTEGRITY_V3_COMPLETE` only after source and tests
prove all named write boundaries are ownership guarded.
