# Codex Review: mw_protocol_p0_word_receipt_producer_20260802

Date: 2026-08-02 (Asia/Shanghai)
Execution: direct Codex bounded implementation and acceptance under the Hermes workflow guard; the guard route metadata was recorded, but no delegated agent was dispatched under the active multi-agent restriction.
Primary run record: `runs/codex_mw_protocol_p0_word_receipt_producer_20260802.md`

## Verdict

**PASS_FOR_BOUNDED_CANONICAL_RECEIPT_PRODUCER_AND_RUNTIME_PROOF; NOT_READY_FOR_PROTOCOL_RELEASE**

## Boundary Check

- Product changes are limited to the controlled Word receipt request/API/repository path and focused tests.
- No historical receipt row, source clone, r42/v36 row, monitoring store, OCR/translation input, stable service, or external provider was touched.
- The canonical PDF was request-only transport data; it was not written to a report, database, or log. The temporary proof root is disposable under `/tmp`.

## Codex Verification

| Check | Evidence | Result |
|---|---|---|
| Contract seam | `canonical_pdf_base64` request field, 50 MB bound, route fail-closed on absence | PASS |
| Canonical recomputation | Server uses `canonical_pdf_page_hashes()` and strict PDF SHA/page/hash comparisons | PASS |
| Audit traceability | Audit detail records contract, renderer/version, DPI, pixel format, page metadata and manifest; no PDF bytes | PASS |
| Historical compatibility | Receipt model/version and existing immutable rows unchanged; repository tests green | PASS |
| Focused automated suite | Word/exporter/API/repository/page-hash tests | 20 passed |
| Syntax | `py_compile` for modified source/contracts | PASS |
| Real HTTP route | Temporary FastAPI on 18935 with artifact/repository fixture | PASS |
| Positive/replay | 200 word_verified then 200 same-key replay | PASS |
| Fail closed | Missing PDF and digest mismatch both 422 before audit write | PASS |
| Restart/stop | One audit after repository restart; port 18935 closed | PASS |

The separate real Microsoft Word/PDF visual gate remains authoritative and was not replaced by this adapter proof.

## Delegated-Agent Output Review

No delegated output was used. The parent inspected the actual source, tests, HTTP evidence, temporary repository/audit state, and listener state. The change is intentionally transport-level and does not claim browser UI acceptance.

## Residual Risk

- No frontend upload control or Word desktop producer is wired in this slice; callers must supply the PDF bytes to the controlled API request.
- A valid canonical hash proves deterministic PDF evidence, not that Microsoft Word produced the PDF; retain the separate Word GUI/PDF visual gate.
- The prior five-store UI fixture exposed a status-path projection write when dependent stores were omitted; that release residual remains open and is explicitly recorded in the Phase 0B UI review.
