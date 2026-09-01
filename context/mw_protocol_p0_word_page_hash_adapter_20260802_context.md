# Task Context: mw_protocol_p0_word_page_hash_adapter_20260802

Created: 2026-08-02 04:32:04
Objective: 标准化医学写作 Word/PDF receipt 的 canonical page-hash adapter，并形成可审计 Protocol release checklist；仅离线 fixture 与聚焦测试，不启动产品 runtime
Task type: `multimodal_document_precheck`
Risk: `high`
Selected agent route: `codex` / `gpt-5.6-luna` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `/Users/smkzw/.codex/AGENTS.md` and workbench `AGENTS.md`.
- `context/mw_protocol_p0_word_native_final_gate_fixture_20260802_context.md`, `runs/codex-subagent_mw_protocol_p0_word_native_final_gate_fixture_20260802.md`, and `reviews/codex_mw_protocol_p0_word_native_final_gate_fixture_20260802_review.md`.
- `services/api/app/medical_writing_document_exporter.py`, `services/api/app/medical_writing_instrument_appendix.py`, `services/api/requirements-medical-writing.txt`, `packages/contracts/workbench_contracts/models.py`, and the Word receipt tests.
- Disposable evidence `/tmp/mw_word_verify.nKvrBb/medical_writing_word_gate_fixture.pdf` plus its rendered page PNGs; no user project or shared runtime.
- External implementation evidence: official pypdfium2 project documentation and repository (Apache-2.0/BSD-3-Clause; fixed render controls available through the public Python API). This is discovery evidence only; the pinned local requirement remains authoritative.

## Scope

- In scope: implement the smallest pure, deterministic adapter that derives canonical per-page hashes from PDF bytes using the existing pinned `pypdfium2==5.12.1` dependency; include explicit contract/version, DPI, dimensions, color mode, and pixel bytes in the digest preimage; add focused tests for determinism, page ordering, malformed/empty PDF fail-closed behavior, and the real disposable PDF fixture; add a compact release checklist/decision record.
- In scope: offline fixture verification and source-level contract review only.
- Out of scope: starting a product service, Microsoft Word UI, live API/DB, runtime artifact storage, provider/model/OCR/translation, source clone/r42/v36, medical monitoring, Synopsis/CSR, or final multi-provider testing.

## Success Criteria

- A named adapter and contract version exist in an allowed product module and return one lowercase SHA-256 per PDF page plus auditable render metadata.
- Same PDF bytes and adapter parameters produce identical hashes across repeated calls; page order/count and dimensions are explicit; malformed/non-PDF input fails closed.
- The adapter uses only the already pinned open-source dependency and does not add network or secret behavior.
- Focused tests pass under the supported Python environment, including the real two-page fixture; no existing Word receipt contract regression is introduced.
- A release checklist explicitly requires adapter contract/version, renderer version, DPI, pixel format, hash list, full PDF hash, screenshot hashes, Word workflow, source/DOCX/snapshot identity, receipt persistence/idempotency, artifact retention/access, and rollback/monitoring before Protocol release.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- Do not silently redefine existing receipt hashes. The new adapter is the canonical producer for new receipts; legacy fixture hashes remain evidence only and are not rewritten.
- Do not claim that a deterministic page hash proves visual quality; visual Word/PDF acceptance remains a separate real-Word gate.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-02 04:32:04: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-02 04:33:00: Re-anchored the residual risk from the Word fixture: page hashes were previously created by a one-page pypdf serialization and lacked a production adapter. Bounded discovery selected the already pinned pypdfium2 renderer; no new dependency or network operation is authorized.
- 2026-08-02 04:38:00: Added `services/api/app/medical_writing_pdf_page_hash.py`. The adapter is fixed to contract `medical_writing_pdf_page_hash_v1`, `pypdfium2==5.12.1`, 200 DPI, PDFium `RGB8` bitmap bytes, explicit page dimensions/stride, and a canonical JSON header before SHA-256. It fails closed on non-PDF, malformed, oversized, page-count, renderer-version, and non-RGB output conditions.
- 2026-08-02 04:39:00: Added focused tests in `tests/test_medical_writing_pdf_page_hash.py` for repeated-call determinism, ordered pages/metadata, order-sensitive manifest identity, malformed/non-bytes rejection, and the disposable Word/PDF fixture. The adapter does not rewrite or validate legacy receipt rows; it is the producer contract for new evidence.
- 2026-08-02 04:40:00: `/usr/bin/python3 -m pytest -q tests/test_medical_writing_pdf_page_hash.py tests/test_medical_writing_word_verification.py tests/test_medical_writing_word_verification_api.py` passed `14 passed` (17 existing deprecation warnings), including renderer-version drift fail-closed. `py_compile` passed for the adapter and tests.
- 2026-08-02 04:40:20: Real disposable fixture `/tmp/mw_word_verify.nKvrBb/medical_writing_word_gate_fixture.pdf` produced two canonical hashes: page 1 `2d7ba50d8fb3e3dff3ae7a4e1d0794b284f786d04e09594d49516cefc9a644cc`; page 2 `364dc6590f6dbfa1ba1cd92b3dc26246e57e1c1e7d07b4ef8ce6a6e96336a2de`; full PDF `d3da7babaac3a78abe3123c7fee120632c1f1a1fd44d2b4d0e7f83a97c9adcc`; canonical page manifest `6c3c49d858c7eca893c37840ae07b06133903adc643473fbf60fb6faf2a56c63`. Both pages are A4 at 1654×2339 RGB pixels, 4962-byte row stride, 200 DPI.

## Canonical page-hash release checklist (required before Protocol release)

- [x] Adapter contract/version, pinned renderer version, fixed DPI, RGB8 pixel format, dimensions and row stride are encoded in the hash preimage.
- [x] Full-PDF SHA-256 and ordered per-page hashes are available; the manifest binds both identities.
- [x] Determinism and fail-closed malformed/version/page-count tests pass; real two-page fixture was exercised.
- [x] Existing legacy fixture/receipt evidence is preserved and not rewritten.
- [x] The controlled receipt producer route now calls this adapter for every new API submission through request-only `canonical_pdf_base64`, recomputes PDF/page hashes, and persists only contract metadata in the immutable audit detail. No PDF bytes are retained; no historical receipt row is rewritten.
- [ ] Runtime artifact-root access/retention, actor authentication/e-signature, and rollback/monitoring must be proven.
- [ ] A real Word/PDF gate must still visually inspect every page; canonical hashes are integrity evidence, not visual-QC proof.
- [ ] Only after the above are accepted may Protocol runtime promotion and final multi-provider E2E testing begin.
