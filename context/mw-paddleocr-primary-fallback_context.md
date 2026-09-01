# Task Context: mw-paddleocr-primary-fallback

Created: 2026-07-30 10:45:53
Objective: 医学写作语料准备切换为 PaddleOCR-VL-1.6 官方异步 API 首选、oMLX GLM-OCR 回退；复用既有 OCR；混合 OCR 经翻译辅助 LLM 一致性 QC；语料库仅接纳 Protocol
Task type: `finite_code_task`
Risk: `high`
Selected agent route: `aishuo` / `cms-model` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- User requirement in the active Codex task (2026-07-30):
  - OCR primary: PaddleOCR-VL-1.6 official async Job API.
  - OCR fallback: local oMLX GLM-OCR-bf16.
  - Existing completed OCR evidence must be reused without re-OCR.
  - Mixed-model OCR within one document requires focused consistency QC by
    the translation-support LLM (DeepSeek V4 Flash).
  - Competitor corpus construction uses Protocol only; standalone SAP is not
    downloaded, prepared, translated, or admitted as corpus evidence.
  - The user supplied a Paddle API credential to Codex. It is secret and must
    not appear in source, prompts, logs, reports, tests, fixtures, or stdout.
- Paddle official transport contract supplied by the user:
  - POST `https://paddleocr.aistudio-app.com/api/v2/ocr/jobs`
  - GET `/api/v2/ocr/jobs/{jobId}` until `done` or `failed`
  - model `PaddleOCR-VL-1.6`
  - result is JSONL at `data.resultUrl.jsonUrl`
- Current product source:
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
- Current focused tests:
  - `tests/test_ai_role_runtime_settings.py`
  - `tests/test_ai_runtime_settings.py`
  - `tests/test_ocr_gateway.py`
  - `tests/test_omlx_transport_gate_boundary.py`
  - `tests/test_writing_reference_ocr_evidence.py`
  - `tests/test_writing_reference_preparation_batch.py`
  - `tests/test_medical_writing_corpus_analysis_ai.py`
  - `tests/test_frontend_ai_role_settings_contract.py`
- Frozen runtime r42 is evidence only and must not be mutated by this source
  change. New-source acceptance belongs to a later clean runtime round.

## Scope

- In scope:
  - Add a dedicated Paddle official asynchronous OCR transport that never
    assumes OpenAI chat-completions semantics.
  - Add a provider preset/profile and make Paddle the default OCR binding for
    new role settings while preserving an explicit user-selected binding.
  - Add deterministic fallback to the existing oMLX GLM OCR gateway only
    after a Paddle terminal/request failure, with actual per-page model and
    fallback provenance.
  - Preserve already completed extraction/OCR rows and skip them during retry.
  - Add mixed-model OCR detection and a focused translation-support-LLM QC
    gate with durable, auditable result before corpus use.
  - Restrict preparation and corpus analysis to `protocol` plus the Protocol
    portion of `protocol_sap`; exclude standalone `sap`.
  - Update user-facing preparation/progress language to “研究方案/Protocol”.
  - Add focused deterministic tests; no live credential in tests.
- Out of scope:
  - Re-running or modifying frozen r42.
  - Re-OCR of completed source artifacts.
  - Translating SAP for the competitor protocol corpus.
  - Changing Hy-MT2 body translation or the four-role AI configuration model.
  - Security hardening unrelated to the functional OCR route.

## Success Criteria

- Paddle adapter tests cover submit, pending/running progress, done JSONL
  parsing, result image/markdown handling boundary, timeout, and failed job.
- Primary/fallback tests prove Paddle is attempted first, GLM is called only
  after a verified Paddle failure, and actual model/fallback provenance is
  persisted per OCR page.
- Reuse tests prove completed extraction/OCR evidence is not reprocessed after
  provider switching; only unfinished/retryable work is resumed.
- Mixed Paddle/GLM document evidence triggers exactly one focused Flash
  consistency-QC path before corpus admission; single-model documents do not.
- Standalone SAP is absent from preparation scope and corpus evidence; a
  `protocol_sap` artifact is accepted only as a protocol-bearing source.
- Existing four-role settings UI remains separate and keeps the required
  recommendation text.
- Focused tests, broader medical-writing backend tests, frontend contract
  tests, and frontend build pass.
- A new clean frozen runtime round demonstrates the configured Paddle primary
  route without exposing the credential.

## Risk Boundaries

- Write only inside this workbench workspace.
- Never include the supplied Paddle bearer token or any credential value in
  source, tests, fixtures, prompts, stdout, reports, screenshots, or records.
- Use dependency injection/fakes for Paddle unit and integration tests.
- Do not mutate or claim PASS for frozen r42.
- Preserve immutable OCR evidence and source-artifact lineage.
- Do not allow fallback to be mislabeled as Paddle in persisted evidence.
- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-30 10:45:53: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-30 10:47: Current source inspection found two contract gaps:
  new OCR evidence validation is hard-coded to GLM and competitor preparation
  plus corpus analysis still admit standalone SAP.
- 2026-07-30 10:52: Bounded external verification used official PaddleOCR
  documentation. It confirms that PaddleOCR-VL-1.6 is a document-parsing model,
  the hosted service is asynchronous, official clients expose submit/status/
  wait operations, and document parsing returns per-page Markdown plus related
  resources. The local workbench does not currently install the `paddleocr`
  Python package, so the selected integration is a small injectable HTTP
  adapter for the user-supplied Job API contract rather than adding a large
  runtime dependency. No credential was used or recorded during discovery.
- 2026-07-30 10:58: A1 froze r42 without source mutation or PASS. The last
  visible checkpoint was 82/91 (91%), current file
  `NCT04456673 / Prot_000.pdf`, OCR page 18/115 with 7/8 selected pages
  completed. The UI had no confirmed safe-cancel control, so the tester did
  not kill services or edit the database. r42 remains evidence-only.
- 2026-07-30 11:03: The user observed continued GLM-OCR calls. Root cause:
  frozen r42 API had retained its startup-time GLM binding and its background
  preparation worker continued after the browser tester stopped. Codex sent
  SIGTERM and confirmed PID 88514 exited during graceful shutdown. The
  persisted r42 database/evidence remains intact; that runtime can no longer
  originate GLM calls.
- 2026-07-30 11:19: Completed a separate read-only disk triage and then
  precisely removed only regenerable `writing_reference_artifacts` caches from
  frozen superseded rounds r11/r15/r20/r38/r39/r40. Released approximately
  6.99 GiB. Preserved every database, screenshot, trace, defect record,
  handoff, frontend snapshot, and all r42 recovery assets. Detailed evidence:
  `context/mw_disk_cleanup_triage_20260730.md`.
- 2026-07-30 11:24-11:48: Codex reviewed the delegated source rather than
  accepting its report. It found three material gaps: the Paddle adapter used
  a self-invented JSON/base64 contract instead of the official multipart Job
  API; the extraction bridge discarded actual provider/fallback metadata; and
  the mixed-model consistency-QC module was not called by production code.
- 2026-07-30 11:31: Reworked the Paddle adapter against the supplied official
  local-file contract: multipart fields `model`, `optionalPayload`, and
  `file`; nested `data.jobId`, `data.state`, `data.resultUrl.jsonUrl`, and
  official nested JSONL `result.layoutParsingResults[].markdown.text`.
  Submit/poll/result transport failures now become bounded Paddle failures and
  can trigger the configured GLM fallback. Timeout evidence retains the job
  identifier. No credential value entered source, tests, stdout, or records.
- 2026-07-30 11:37: Preserved actual per-page provider/model/fallback metadata
  from the OCR gateway through extraction and immutable evidence persistence.
  Added durable mixed-OCR QC outcome to the extraction record and wired exactly
  one translation-support-LLM check when a document contains more than one OCR
  model. Non-pass mixed-OCR evidence is excluded from corpus analysis.
- 2026-07-30 11:41: The persisted machine OCR binding was still the old
  `ocr__local_omlx / GLM-OCR-bf16`, independently explaining continued GLM
  use after source changes. Migrated the active role binding to
  `ocr_paddle_official / PaddleOCR-VL-1.6`. The Paddle credential is not yet
  present in the encrypted local credential store, so the role now fails
  closed as not configured instead of silently selecting GLM. GLM remains
  callable only as the explicit post-Paddle failure fallback.
- 2026-07-30 11:44: Updated the four-role settings UI so Paddle's Base URL is
  described as the official async Job endpoint rather than as OpenAI
  compatible, and removed the irrelevant visual-model probe button for the
  specialized Paddle route.
- 2026-07-30 11:48: Verification passed: 119 role/oMLX/contract/OCR/preparation
  unittests, 52 corpus-analysis tests, 37 frontend-role/runtime/OCR transport
  tests, and the Vite production build (1910 modules). Expected test-only
  callback-error logging and FastAPI deprecation warnings were observed;
  neither is a test failure.

## Current Recovery Point

- Source and persisted role binding now select Paddle primary.
- No old r42 API process remains capable of issuing GLM calls.
- Live Paddle verification is pending secure credential entry into the
  existing encrypted local credential store; do not place the supplied bearer
  value in a shell command, test, prompt, report, screenshot, or source file.
- After live Paddle proof, start a clean runtime round (r43 or later). Do not
  resume r42 as source acceptance.

## Subsequent Integration Notes

- 2026-07-30 11:46: Protocol-only scope was consolidated into
  `writing_reference_protocol_scope.py`. The same deterministic boundary now
  gates translation-batch spans and corpus-analysis evidence. Standalone SAP
  cannot enter the competitor corpus; combined files contribute only the
  explicitly bounded Protocol portion.
- 2026-07-30 11:49: Current-source services were restarted and browser
  build-hash compatibility was re-established. Paddle remains the selected OCR
  role and GLM remains only the explicit post-Paddle-failure fallback. No OCR
  rerun was initiated in this slice.
