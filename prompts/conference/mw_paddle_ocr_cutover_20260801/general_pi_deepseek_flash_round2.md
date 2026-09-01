This is continuation round 2 in the same Pi/DeepSeek session. Do not restart
the task, open a new session, edit files, run tests, start services, or inspect
another participant's output.

## Hard boundaries

- Work only inside the current workbench (`.`).
- This is read-only review; do not modify source or runtime state.
- Return the complete report; never write the runner-owned report with tools.
- Never write the runner-owned report with tools.

Read these files only:
- `AGENTS.md`
- `context/mw_paddle_ocr_cutover_20260801_conference_context.md`
- `plans/codex_main_venue_mw_paddle_ocr_cutover_20260801.md`
- `packages/contracts/workbench_contracts/models.py`
- `services/api/app/main.py`
- `services/api/app/paddle_ocr_adapter.py`
- `services/api/app/ocr_fallback_orchestrator.py`
- `services/api/app/writing_reference.py`
- `services/api/app/writing_reference_preparation_batch.py`
- `tests/test_paddle_ocr_primary_fallback.py`
- `tests/test_writing_reference_preparation_batch.py`

Runner-managed output path:
`runs/conference/mw_paddle_ocr_cutover_20260801/general_pi_deepseek_flash.md`

Your initial pass identified actionable gaps while Codex was still changing the
bounded implementation. Re-anchor only to the latest current filesystem and
the updated conference context/plan. Perform a delta-only read-only review of
these completed remediations:

1. Durable batch-item OCR model pin with current-row and attempt validation.
2. `PaddleOcrOutcomeUnknownError` for submit 5xx/URLError and all
   post-acceptance poll/result/timeout/empty ambiguity.
3. Direct error-code mapping plus retry-selection and worker-claim exclusion.
4. Paddle-pinned running extraction recovered after process restart as
   outcome-unknown rather than generically retryable.
5. Only explicit 4xx rejection or terminal remote `failed` may transfer to GLM.
6. Hosted concurrency hard-clamped to 1..4; invalid configuration returns 4.
7. 429-only submit retry, numeric/HTTP-date parsing, and a 30-second delay cap.
8. Codex reports 105 focused tests passed and compileall passed; do not rerun.

Separate current bounded-cutover blockers from later availability enhancements
such as automatic remote-job resumption, safe GET retry, latent unused chapter
OCR paths, or broader provenance hardening. Return the complete updated schema
for `general_pi_deepseek_flash` with a clear READY/NOT READY and only current
P0-P4 issues. Keep evidence, inference, recommendation, and uncertainty
separate. Codex remains final authority.
