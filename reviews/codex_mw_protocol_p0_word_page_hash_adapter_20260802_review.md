# Codex Review: Canonical Word/PDF Page-Hash Adapter

Date: 2026-08-02 (Asia/Shanghai)
Delegated-agent output: none; Codex implemented and verified the bounded adapter directly after guard initialization.
Verification: source review, focused pytest, py_compile, and the real disposable two-page PDF fixture were completed. No API/service or Word UI was started in this pass.
Hermes workflow guard: task initialization, prompt preflight, and review-gate boundaries were followed; the guard route metadata was retained as an audit record, not treated as acceptance authority.

## Verdict

**PASS FOR BOUNDED CANONICAL HASH ADAPTER; NOT READY FOR PROTOCOL RELEASE.**

## Boundary Check

- Product change was limited to the new adapter module and its focused test file; task context/run/review/metrics were updated.
- No production service, shared runtime database, provider, model, OCR/translation pipeline, source clone, r42/v36 row, or medical-monitoring file was touched.
- Legacy receipt rows and the prior Word fixture hashes were not rewritten. The adapter's output is a new explicit contract, not a retroactive reinterpretation.

## Codex Verification

- `14 passed` across the adapter, Word receipt contract, and Word receipt API tests; only existing deprecation warnings remained.
- `py_compile` passed for source and test files.
- Repeated calls on the static two-page PDF returned equal ordered objects; manifest changes when full PDF identity or page order changes; malformed/non-bytes inputs fail closed.
- The real disposable Word/PDF fixture produced two deterministic canonical RGB8 page hashes and a full-PDF-bound manifest. Prior Word visual QC evidence shows the same two pages were visually intact; this adapter does not replace that gate.
- The adapter pins `pypdfium2==5.12.1`, already present in `services/api/requirements-medical-writing.txt`; no dependency or network write was introduced.

## Residual Risk and release checklist

The receipt producer/UI still needs to call this adapter and persist its contract metadata for every new receipt; the current server route receives user-supplied hashes and cannot independently derive them without the PDF artifact. Runtime artifact access/retention, actor authentication/e-signature, rollback/monitoring, and a real Word/PDF gate remain open. These are recorded as explicit checklist items in the task context.

Final review state: `READY_FOR_BOUNDED_PHASE0C_CONTINUATION`, `NOT_READY_FOR_PROTOCOL_RELEASE`.

## Superseding producer integration note

The previously open producer item is now covered by `mw_protocol_p0_word_receipt_producer_20260802`: the controlled API accepts request-only canonical PDF bytes, invokes this adapter server-side, compares the submitted receipt's PDF/page hashes, and records only adapter metadata in the immutable audit detail. The new slice passed its focused suite and disposable HTTP proof. Runtime artifact access/retention, actor authentication/e-signature, rollback/monitoring, and the separate real Word visual gate remain open; Protocol release is still not authorized.
