You are Hermes running inside a Codex-controlled workflow.

First, fully read and comply with `/Users/smkzw/.hermes/SOUL.md`. In your output, include one sentence saying whether you read the full file. Do not claim this unless you actually read it.

Hard boundaries:
- Work only inside the runner-provided current workbench workspace.
- Do not read or modify production paths.
- This is an authorized edit round. Make the bounded source and test changes
  described below directly in the workspace.
    - Tools are available and must not be disabled. Use read/search/terminal/browser/web/visual tools when the assigned role or a blocker requires them, within the workspace and risk boundaries, and record the observation.
    - Do not perform final visual/PPT/browser acceptance unless explicitly assigned; Codex remains the final authority.
- Runner-managed output path: `runs/hermes_mw-paddleocr-primary-fallback.md`. Never invoke a
  write/edit tool on this report path; return the complete report in your final
  response and let the runner persist it.

Read these files only:
- `context/mw-paddleocr-primary-fallback_context.md`
- `services/api/app/main.py`
- `services/api/app/ocr_gateway.py`
- `services/api/app/ai_runtime_settings.py`
- `services/api/app/ai_role_runtime_settings.py`
- `services/api/app/writing_reference.py`
- `services/api/app/writing_reference_ocr_evidence.py`
- `services/api/app/writing_reference_preparation_batch.py`
- `services/api/app/medical_writing_corpus_analysis_ai.py`
- `services/api/app/chapter_translation_pipeline.py`
- `packages/contracts/workbench_contracts/models.py`
- `tests/test_ai_role_runtime_settings.py`
- `tests/test_ai_runtime_settings.py`
- `tests/test_ocr_gateway.py`
- `tests/test_omlx_transport_gate_boundary.py`
- `tests/test_writing_reference_ocr_evidence.py`
- `tests/test_writing_reference_preparation_batch.py`
- `tests/test_medical_writing_corpus_analysis_ai.py`
- `tests/test_frontend_ai_role_settings_contract.py`

Task:
Implement the complete bounded slice in the task context:

1. Add a dedicated PaddleOCR-VL-1.6 official async Job API adapter. Do not
   pretend it is OpenAI-compatible. Keep HTTP/polling/parsing injectable and
   deterministic in tests. Never hardcode or request a live credential.
2. Add the Paddle official provider preset/profile and default it for new OCR
   role settings without overwriting an explicit existing user choice.
3. Add Paddle-primary -> oMLX GLM fallback. Fallback may occur only after a
   verified Paddle request/terminal failure. Persist the actual per-page model,
   provider/profile identity, and fallback reason; never label GLM output as
   Paddle.
4. Preserve completed OCR/extraction evidence across a provider switch and
   resume only unfinished/retryable work. Use current durable item/extraction
   semantics; do not mutate immutable rows.
5. When one document contains OCR evidence from more than one model, invoke a
   focused translation-support LLM consistency-QC stage exactly once before
   corpus use. Persist a bounded audit outcome. Single-model evidence must not
   trigger it. The QC model must not rewrite OCR text.
6. Restrict competitor corpus work to Protocol. Exclude standalone SAP from
   preparation and corpus analysis. `protocol_sap` may remain eligible only
   because it contains a Protocol; ensure the corpus evidence path does not
   treat a standalone SAP section as a protocol wording source.
7. Update preparation/progress user-facing wording from Protocol/SAP to
   Protocol/研究方案 where this workflow is specifically the corpus builder.
8. Add focused tests for every success criterion, run them, then run the
   reasonably broad medical-writing regression set that fits the time budget.

Prefer a small coherent implementation. Do not refactor unrelated paths.
Return exact changed files, commands, results, unresolved risks, and what
Codex must verify in the live product.

Output schema:
1. `# Hermes Execution Handoff: mw-paddleocr-primary-fallback`
2. `## Boundary Check`
3. `## Files Changed`
4. `## Implementation`
5. `## Verification`
6. `## Failed Paths And Residual Risk`
7. `## Codex-Owned Verification`

Quality gates:
- Do not expose any credential or secret.
- Do not claim live Paddle success from mocked tests.
- Do not claim provider-switch reuse unless a deterministic test proves it.
- Do not claim SAP exclusion unless preparation and corpus-analysis tests prove it.
- Do not make final clinical/regulatory/visual/current-web claims.
- Keep final acceptance with Codex.
