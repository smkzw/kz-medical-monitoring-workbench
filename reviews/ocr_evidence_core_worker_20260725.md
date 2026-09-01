# Reference OCR evidence core bounded worker record

Date: 2026-07-25

## Scope and result

Implemented only the OCR extraction/evidence slice. No contracts, repository,
API route, translation pipeline/batch, frontend, or runtime configuration was
changed.

New OCR extraction revisions now:

- require the exact `GLM-OCR-bf16` model;
- render every selected page at exactly 200 DPI;
- keep OCR execution at no more than 8 concurrent calls;
- wait for the complete OCR batch before publishing any final sidecar;
- write one immutable PNG sidecar per selected page beneath the source
  artifact directory;
- record a recomputable PNG SHA-256, byte count, pixel dimensions, relative
  path, OCR text SHA-256, character count, profile digest, selection reason,
  result status, and optional span lineage;
- retain `empty_text` evidence with the SHA-256 of empty UTF-8 text and no
  source span;
- replace an anomaly page's native span only when OCR actually recovered
  text. Empty anomaly OCR keeps the native text and records the attempted OCR
  evidence.

Legacy extraction rows remain readable through the already accepted
`legacy_metadata_only` contract. New writes use an explicit strong validator
and cannot silently fall back to the legacy defaults.

No page-by-page approval, `待医学批准`, security/rights approval, or new
workflow gate was introduced. Existing basic content exception and medical
manager override behavior was not changed.

## Implementation details

`services/api/app/writing_reference_ocr_evidence.py` owns:

- deterministic sidecar path construction;
- safe artifact-root-relative resolution;
- PNG signature/IHDR dimension validation;
- hash-bound immutable creation with exact-replay support and overwrite
  rejection;
- strong validation for new OCR evidence records.

`WritingReferenceExtractionService` now passes the registered source artifact
relative path into OCR recovery, calculates image evidence during sequential
rendering, runs the injectable OCR adapter concurrently, publishes sidecars
only after all calls return, and constructs typed
`WritingReferenceOcrPageEvidence` records in physical-page order.

Tests use only fake OCR adapters. No real-model success is claimed.

## Verification

Passed:

```text
python3 -m py_compile \
  services/api/app/writing_reference_ocr_evidence.py \
  services/api/app/writing_reference.py \
  tests/test_writing_reference_ocr_evidence.py
```

Focused and adjacent suite:

```text
python3 -m pytest -q \
  tests/test_writing_reference_ocr_evidence.py \
  tests/test_writing_reference_extraction_service.py \
  tests/test_writing_reference_extraction.py \
  tests/test_writing_reference_upper_layer_contracts.py \
  tests/test_chapter_translation_pipeline.py \
  tests/test_writing_reference.py
```

Result: `120 passed`, with only existing PyMuPDF SWIG deprecation warnings.

Broader `tests/test_writing_reference*.py` result: `213 passed, 2 failed`.
Both failures reproduce independently and are outside this bounded write set:

1. `test_trusted_internal_policy_accepts_only_pinned_translation_context`
   still constructs the now-rejected legacy `openai_compatible/configured-model`
   route instead of the product-owned DeepSeek route.
2. `test_http_core_contract_and_span_injection_rejection` immediately expects
   a newly accepted asynchronous translation batch to report `completed`, but
   the current API returns `accepted`.

No out-of-scope files were changed to mask these failures.

## Residual real OCR release gate

Still required before product acceptance:

1. Run the real local oMLX `GLM-OCR-bf16` adapter on representative native,
   scanned, mixed-text, table, figure, and empty pages at 200 DPI.
2. Recompute every stored PNG hash and dimension from disk after process
   restart.
3. Confirm actual adapter response text, empty-page behavior, concurrency,
   retry/failure behavior, and profile lineage without substituting an Agent's
   own OCR.
4. Execute the accepted CRSwNP `NCT02898454` and UC `NCT02819635` batches,
   including the predefined UC OCR page set, and perform clinical/visual
   evidence review.
5. The read-only evidence API and user-facing exception review remain a later
   integration slice; this worker intentionally did not modify `main.py` or
   repository/API surfaces.

## Modified files

- `services/api/app/writing_reference_ocr_evidence.py`
- `services/api/app/writing_reference.py`
- `tests/test_writing_reference_ocr_evidence.py`
- `reviews/ocr_evidence_core_worker_20260725.md`
