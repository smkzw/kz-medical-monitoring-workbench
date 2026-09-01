Continue the same session. Your first pass consumed its answer budget while
reading and made no edits. Do not repeat broad reads and do not return a plan.

Implement now. Work in this order:

1. Create the small official Paddle async Job adapter and its deterministic
   unit tests. Use only the user-supplied endpoint contract already recorded in
   context. Never use or print a live token.
2. Wire a Paddle provider preset/builtin profile, new-install OCR default, and
   Paddle-primary -> oMLX GLM fallback. Extend OCR results/evidence so the
   actual page model/provider and fallback reason are persisted.
3. Change preparation and corpus-analysis filters so standalone `sap` is
   excluded while `protocol` and protocol-bearing `protocol_sap` remain.
   Update the directly affected progress strings.
4. Add a minimal durable mixed-model consistency-QC gate before corpus
   analysis, using the existing translation-support provider abstraction.
   It must be read-only over OCR text and skipped for single-model documents.
5. Run focused tests.

Avoid reading all of `main.py` again. Relevant anchors are already known:
`_RoleBoundRemoteOcrGateway`, `_build_role_bound_ocr_gateway`,
`_writing_reference_ocr_runner`, `_recover_pages_with_ocr`,
`ALLOWED_DOCUMENT_TYPES`, `_PROTOCOL_DOCUMENT_TYPES`, and
`_evidence_catalog`.

If one item cannot be completed coherently, finish and test the other items,
then report the exact remaining gap. Do not stop at analysis.
