# r11 Document Preparation Failure Analysis

## Boundary

This record analyzes the frozen `release-r11-20260729` runtime. No runtime
database or r11 evidence was modified.

## Source

- Project: `proj_user_d9cd77c5ef5e`
- Snapshot: `wref_search_9e59d59c6cf7e5a6924d`
- Preparation batch: `wref_prep_421949bdd4c543d72a61470f`
- Frozen SQLite:
  `runs/execution/mw_final_5x3_harness_20260728/rounds/release-r11-20260729/slots/A1/lazy_medical_writer/runtime/writing_reference.sqlite3`

## Observed Distribution

- Public Protocol/SAP documents: 99
- Preparation items:
  - `prepared`: 44
  - `review_required`: 52
  - `failed`: 3
- Persisted validation states:
  - `confirmed`: 44
  - `mismatch`: 45
  - `needs_review`: 7

The earlier A1 handoff counted 59 blocked documents because the pipeline
combines 52 review-required documents with the 3 failed documents and other
admission conditions. The persisted preparation and validation tables above
are the authoritative detailed distribution.

## Root Cause A - Document-Type Overclassification

The deterministic validator in
`services/api/app/writing_reference.py` marks an expected SAP as mismatch
whenever `protocol_strong` is true and `sap_strong` is false. In real
ClinicalTrials.gov material, an SAP commonly repeats protocol language and
M11-like anchors. `sap_strong` is also narrowly gated by a short title span
plus at least two detail phrases. This combination produced 45 mismatches,
including files whose registry metadata and filename identify them as SAP or
Protocol+SAP.

Required repair direction:

1. Treat trusted ClinicalTrials.gov document metadata and filename as
   independent evidence, not merely an expected value to be defeated by a
   weak text heuristic.
2. Distinguish positive contradictory evidence from absence of a strong SAP
   title match.
3. Send genuinely ambiguous cases to the configured comprehensive AI or
   translation-support LLM for structured document-role classification, with
   deterministic evidence and schema validation.
4. Default the AI classification into the batch result and expose one batch
   review, not 52 row-by-row approvals.
5. Preserve a user override with a concise warning when the user knows the
   downloaded file is correct.

## Root Cause B - OCR Reconciliation Without Native Text

Three items failed extraction with:

`reconciled OCR evidence must retain the native text channel`

The implementation in `services/api/app/writing_reference.py` labels every
anomaly page with OCR text as `ocr_reconciled`, even when the page had no
native spans. The validator in
`services/api/app/writing_reference_ocr_evidence.py` correctly requires a
native channel for true reconciliation, so an image-only anomaly page becomes
internally contradictory.

Required repair direction:

1. Use `ocr_reconciled` only when native spans actually exist.
2. Use the ordinary OCR recovery channel for an image-only or zero-native-text
   anomaly page.
3. Preserve current behavior for a true native/OCR reconciliation and for an
   empty OCR result.
4. Add focused regressions for:
   - anomaly + native spans + OCR text;
   - anomaly + no native spans + OCR text;
   - anomaly + native spans + empty OCR;
   - eight-way OCR concurrency unchanged.

## Acceptance Boundary

Neither issue is fixed by the candidate-drawer lifecycle repair. Both require
separate source changes and a fresh isolated E2E round. No override or manual
database mutation may count as a pass.

## Accepted Source Repairs

### OCR channel

- `ocr_reconciled` now requires both native spans and non-empty OCR.
- Image-only anomaly pages use ordinary OCR recovery.
- Codex reran 38 related tests and targeted compilation; accepted.
- Review:
  `reviews/codex_mw-r11-ocr-evidence-channel-fix-20260729_review.md`

### ClinicalTrials.gov document admission

- The official registry `hasProtocol`/`hasSap` identity now takes precedence
  over template-sensitive body heuristics for registry-bound documents.
- Manual/non-registry publication substitution and Protocol/SAP contradiction
  checks remain strict.
- Codex reran 47 related tests.
- Read-only recomputation of all 96 r11 extracted public documents changed the
  old 44 confirmed / 45 mismatch / 7 needs-review distribution to 96 confirmed,
  with no override and no database mutation.
- Decision:
  `context/mw_ctgov_document_type_authority_20260729.md`
- Review:
  `reviews/codex_mw_ctgov_document_admission_20260729_review.md`

Both repairs still require a new isolated r12 runtime. The frozen r11 round
remains permanently blocked.
