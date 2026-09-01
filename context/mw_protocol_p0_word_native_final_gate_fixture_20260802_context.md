# Task Context: mw_protocol_p0_word_native_final_gate_fixture_20260802

Created: 2026-08-02 03:50:09
Objective: 在隔离临时 fixture 上用真实 Microsoft Word Computer Use 完成打开、域更新确认、保存、重开、导出 PDF、页数与页图证据；仅证明 Word receipt 链，不启动医学写作服务，不触碰产品 runtime/upstream/OCR/translation/monitoring 数据。
Task type: `multimodal_document_precheck`
Risk: `high`
Selected agent route: `codex` / `gpt-5.6-luna` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/runs/codex_mw_protocol_p0_phase0c_word_receipt_persistence_20260802.md` and its context/review/metrics are the predecessor boundary.
- Product contracts/helpers: `packages/contracts/workbench_contracts/models.py`, `services/api/app/medical_writing_document_exporter.py`, and `services/api/app/medical_writing_word_verification_repository.py`.
- Isolated fixture source: `/tmp/mw_word_verify.nKvrBb/medical_writing_word_gate_fixture.docx`, with source snapshot `a51665c20c6ba25ba27a9256500a1f2c8bc57e4dcd6b2d4100851fa9f18a30ad`.
- Real Word/PDF evidence: `/tmp/mw_word_verify.nKvrBb/medical_writing_word_gate_fixture.pdf` and `word_gate_page_20260802_reopen-{1,2}.png`.
- Microsoft Word app observed through the Computer Use skill; version `16.111.2 (16.111.26072617)`.

## Scope

- In scope: use Microsoft Word UI on the disposable fixture only; open, accept the field-update warning, save, close/save field changes, reopen, confirm two-page pagination, export PDF through Word UI, render PDF pages for visual QC, and construct/verify a source-bound Word receipt with the isolated repository.
- In scope: direct hashes, page evidence, receipt identity, idempotent replay, restart read, and audit-row count.
- Out of scope: starting the medical-writing service or browser, calling product APIs against live jobs, shared runtime schema/migrations, real user projects, OCR/translation/model work, final multi-provider tests, Synopsis/CSR, and release promotion.

## Success Criteria

- Word UI shows the fixture as two pages before and after close/reopen; no clipping or unexpected page drift is visible in the rendered pages.
- Word exports a two-page PDF; both rendered page images pass visual QC and retain header, TOC/section content, and footer.
- Receipt source snapshot equals the fixture document snapshot, DOCX/PDF/page/screenshot hashes are recorded, and `build_medical_writing_word_verified_preview` returns `preview_status=word_verified` with `estimated=false` pages.
- Isolated SQLite commits exactly one receipt and one audit event; same-key replay is a replay, and a newly constructed repository reads the same receipt.
- No product/runtime/upstream file is changed and no shared runtime database is created.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated route is not final authority; Codex owns verification and acceptance. This pass used Codex direct Computer Use on a disposable `/tmp` fixture; no delegated worker was dispatched.
- The fixture's save-on-close prompt was handled by saving the field updates once, then later discarding only transient post-export field changes so the receipt's final DOCX hash remains stable. The fixture is disposable and not a user document.
- Per-page PDF hashes are deterministic hashes of one-page PDF serializations produced by `pypdf`; the full PDF hash and PNG screenshot hashes are direct file hashes. Production must standardize the page-byte hashing adapter before runtime rollout.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-02 03:50:09: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-02 03:49-03:53: Microsoft Word UI opened the fixture, accepted the update-fields warning, saved, exported a print-quality PDF, closed with field updates saved, reopened from Word recent files, confirmed `第 1 页，共 2 页`, and exported the PDF again after reopen; overwrite confirmation was handled in the Word UI.
- 2026-08-02 03:53: PDF hash `d3da7babaac3a78abe3123c7fee120632c1f1a1fd44d2b4d0e7f83a97c9adcc8`; page count 2; A4 `595.2 x 841.92 pt`; PNG hashes page 1 `73845ca62cc9e50528473e3f6c2f9f26f20fc0898b3a7ddb5e917922d34b2843`, page 2 `4dda1b61f4b1bcc67a02d1a1241bfbb0f15cd31948d9df6ff6924ec1b48a5928`.
- 2026-08-02 03:55: Receipt `word-check-real-20260802-001` committed to `/tmp/mw_word_verify.nKvrBb/word_receipts_real.sqlite3`; first commit `replayed=false`, same-key replay `replayed=true`, same audit id, restart read equal, and audit count `1`.
- 2026-08-02 03:56: Word document closed back to the start window; no product service/browser/OCR/translation process was started.
