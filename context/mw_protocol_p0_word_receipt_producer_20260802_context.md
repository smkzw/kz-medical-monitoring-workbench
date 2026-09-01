# Task Context: mw_protocol_p0_word_receipt_producer_20260802

Created: 2026-08-02 04:58:36
Objective: 将 canonical PDF page-hash adapter 绑定到 Word verification receipt producer，并在隔离 fixture 验证 artifact-bound、幂等、重启、失配 fail-closed；不改变历史 immutable receipt/r42/v36/运行时数据
Task type: `multimodal_document_precheck`
Risk: `high`
Selected agent route: `codex` / `gpt-5.6-luna` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `/Users/smkzw/.codex/AGENTS.md` and the applicable workspace/workbench `AGENTS.md`
- `context/mw_protocol_p0_phase0c_word_receipt_contract_20260802.md`
- `context/mw_protocol_p0_phase0c_word_receipt_persistence_20260802.md`
- `context/mw_protocol_p0_word_native_final_gate_fixture_20260802_context.md`
- `runs/codex_mw_protocol_p0_word_native_final_gate_fixture_20260802.md`
- `runs/codex-subagent_mw_protocol_p0_phase0c_word_receipt_runtime_integration_20260802.md`
- `services/api/app/medical_writing_pdf_page_hash.py`
- `services/api/app/medical_writing_document_exporter.py`
- `services/api/app/medical_writing_word_verification_repository.py`
- `services/api/app/main.py` and `packages/contracts/workbench_contracts/models.py`
- focused Word receipt, repository, API, and canonical page-hash tests under `tests/`
- disposable Word/PDF fixture evidence already recorded under `/tmp/mw_word_verify.nKvrBb`; no source clone or production runtime is an authority for this task.

## Scope

- In scope: make the controlled Word-verification submission route recompute canonical PDFium page hashes from a transport-only base64 PDF; compare PDF digest, page count, and ordered page hashes against the submitted receipt; persist only canonical renderer metadata in the append-only audit detail; preserve idempotency/restart/immutability; add focused tests and a disposable HTTP proof.
- In scope: a request-level `canonical_pdf_base64` transport field with a 50 MB fail-closed limit; no PDF bytes persisted or logged.
- Out of scope: rewriting historical receipt rows, changing the Word receipt schema/version, rerunning Microsoft Word/OCR/translation, starting a stable service, touching r42/v36/monitoring data, adding a frontend upload flow, or entering Synopsis/CSR/final multi-provider testing.

## Success Criteria

- A new submission cannot commit unless the supplied PDF's SHA-256, canonical page count, and ordered page hashes exactly match the receipt.
- Adapter identity/renderer/version/DPI/pixel format, page metadata, PDF digest, and canonical manifest are returned and auditable without retaining PDF bytes.
- Missing, malformed, oversized, renderer-drift, PDF-digest mismatch, page-count mismatch, and page-hash mismatch all fail closed before repository write.
- Existing immutable receipt rows remain readable; repeated same-key requests replay one receipt/audit event; restart and concurrent repository behavior remain green.
- Focused tests and py_compile pass; the isolated HTTP proof uses a temporary artifact/repository and is stopped/closed after verification.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- Direct Codex implementation is used for this bounded slice; no external or native sub-agent is dispatched under the current multi-agent restriction. Guard route metadata remains recorded, but no delegated confidence is treated as acceptance.
- The base64 PDF is request-only; never copy it into a report, log, persistent database, or source artifact. Do not claim that the adapter can replace the separate real Microsoft Word visual gate.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-02 04:58:36: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-02 05:01:00: Read existing page-hash/Word receipt contracts and the prior real Word/PDF + HTTP evidence. Chose a minimal transport-bound integration: request supplies base64 PDF; server recomputes canonical hashes; audit stores only computed metadata.
- 2026-08-02 05:08:00: Added `canonical_pdf_base64` to the controlled submit request, canonical recomputation and fail-closed comparisons in the API route, and canonical metadata in the append-only audit detail. No historical rows are migrated or rewritten.
- 2026-08-02 05:11:00: Updated the focused API test to use the deterministic two-page PDF fixture; success response exposes adapter identity and audit records page count. Added missing-PDF and digest-mismatch fail-closed checks.
- 2026-08-02 05:12:00: Focused Word receipt/API/repository/page-hash suite passed `19 passed`; review and disposable HTTP proof remain to be completed.
- 2026-08-02 05:16:00: After adding digest-mismatch coverage, the focused suite passed `20 passed`. A disposable real HTTP proof on port 18935 returned 200/word_verified, 200/same-key replay, 422/missing canonical PDF, and 422/PDF digest mismatch; repository restart read one receipt and one canonical audit event; the port was closed. Evidence: `/tmp/mw_word_canonical_runtime.9Rdylp/runtime_canonical_evidence.json`, SHA-256 `93e803903a645c44a3571f41b2c43b8cfd6477026705a95bb4b17a3623e6623f`.
- 2026-08-02 05:17:00: Bounded verdict `READY_FOR_CANONICAL_RECEIPT_PRODUCER_AND_RUNTIME_PROOF; NOT_READY_FOR_PROTOCOL_RELEASE`. Next safe action is to close the producer/runtime gate into the broader Protocol release checklist; do not enter Synopsis/CSR or final multi-provider testing.
