# CMS Backend Remediation Round 5

Continue the same CMS execution session. Round 4 made useful production edits,
but Codex source review and adjacent tests prove the backend is not yet
acceptable. Finish the production contract and migrate the deterministic test
fixtures to the required composite pipeline. Do not merely weaken assertions.

Before acting, reread `/Users/smkzw/.hermes/SOUL.md`,
`/Users/smkzw/.codex/AGENTS.md`, project `AGENTS.md`, the current task record,
and the current source. Treat previous reports as evidence, not truth.

## Read these files only as the initial context

- `/Users/smkzw/.hermes/SOUL.md`
- `/Users/smkzw/.codex/AGENTS.md`
- `AGENTS.md`
- `records/active_slices/medical_writing_cross_indication_reference_gate_20260718/TASK_RECORD.md`
- `records/active_slices/medical_writing_cross_indication_reference_gate_20260718/ACCEPTANCE_CONTRACT.md`
- `services/api/app/writing_reference.py`
- `services/api/app/chapter_translation_pipeline.py`
- `services/api/app/writing_reference_translation_batch.py`
- `services/api/app/main.py`
- `services/api/app/regulatory_translation_glossary.py`
- `tests/test_mw_round3_backend_remediation.py`
- `tests/test_writing_reference_extraction.py`
- `tests/test_writing_reference_extraction_service.py`
- `tests/test_chapter_translation_pipeline.py`
- `tests/test_writing_reference_translation_service.py`
- `tests/test_writing_reference_translation_batch.py`
- `tests/test_writing_reference_api.py`

## Codex-observed test evidence

Focused command:

`python3 -m pytest -q tests/test_mw_round3_backend_remediation.py`

Actual result: `11 passed`.

Adjacent command:

`python3 -m pytest -q tests/test_writing_reference_extraction.py tests/test_writing_reference_extraction_service.py tests/test_chapter_translation_pipeline.py tests/test_writing_reference_translation_service.py tests/test_writing_reference_translation_batch.py tests/test_writing_reference_api.py`

Actual result: `21 failed, 59 passed`.

The failures include six stale assertions/signatures, but fifteen service and
batch failures occur because old deterministic fixtures instantiate
`WritingReferenceTranslationService` and batch services without the now
mandatory composite pipeline. Production must remain fail-closed. Update those
fixtures to inject a deterministic Flash-plan -> Hy-MT2 -> Flash-QC pipeline so
the existing behavioral assertions still exercise translation, revision,
fidelity blocking, review, retry, audit and batch projection.

## Additional production defects found by Codex

1. `_generate_with_composite_pipeline()` receives `user_instruction`, including
   medical-review return comments, but ignores it. The user instruction and
   current medical-review comment must influence the planner/translation/QC
   contract and be covered by tests.
2. The legacy path renders actual matching glossary terms through
   `render_regulatory_translation_glossary_contract(span.source_text)`. The
   composite path currently passes only the glossary version string to Hy-MT2.
   Pass the rendered, source-matched bilingual term contract to Hy-MT2 and the
   Flash integration stage. Preserve the version separately in lineage.
3. Anomaly-page reconciliation removes native spans, but the persisted
   `ocr_recovery_pages` entry currently contains no native text/hash/span
   lineage despite comments claiming that native content is retained. Persist
   both native and OCR channels, with native span IDs, locators and text hashes
   or an equivalent immutable auditable structure. Downstream translation uses
   the reconciled OCR span only; do not admit duplicate facts.
4. Flash QC currently allows empty `integrated_text` and silently substitutes
   the raw Hy-MT2 body. A passed result must include a non-empty complete
   integrated candidate. Empty/missing integrated text fails closed. The final
   text/hash must be computed from that candidate.
5. `detect_anomaly_pages()` must be tested with an actual synthetic PDF whose
   text-bearing numeric/unit line contains a small vector glyph. The test must
   prove the non-empty-text page is routed to OCR and both channels are
   retained. Avoid hardcoding indication, LDH or page number.
6. Blank/scanned low-level extraction may return zero spans for OCR recovery,
   but the extraction service without an OCR runner must still fail explicitly
   before content validation. A fully scanned 28-page document with a wired OCR
   runner must process all pages with active OCR calls <=8.
7. Preserve one authoritative production service/pipeline instance in
   `main.py`, item-scoped progress, route/response contracts, retry semantics,
   medical review and admission behavior.

## Required tests

- Repair all 21 adjacent failures by preserving the intended product behavior.
- Add focused tests for:
  - medical-review comment and explicit user instruction reaching the composite
    adapters;
  - rendered glossary terms, not only the version label, reaching Hy-MT2 and
    Flash QC;
  - passed Flash QC with empty integrated text failing closed;
  - synthetic vector-glyph anomaly routing plus dual-channel lineage;
  - fully scanned 28-page OCR concurrency <=8;
  - direct and batch final text/hash coming from the Flash-integrated candidate;
  - malformed planner/QC payloads failing closed.
- Replace the stale “reject more than 8 total OCR pages” assertion with proof
  that all pages run while active concurrency never exceeds 8.
- Update the legacy payload expectation to the current honest empty stage, not
  a fabricated active `extracting` state.

Run the focused Round 3/Round 5 tests and all six adjacent files above. Continue
until they are green. Then run the broader writing-reference test selection
discoverable by `rg --files tests | rg 'writing_reference|chapter_translation'`.

## Hard boundaries

- Do not modify frontend files, stable runtime databases, real clinical source
  files, credentials or unrelated modules.
- Do not restore the Flash-only body translation fallback.
- Do not replace GLM-OCR-bf16, Hy-MT2 or DeepSeek Flash.
- Do not claim live three-indication E2E or release acceptance.
- Source and test edits are authorized. Reports are not acceptance evidence.

Write exactly one output file:
`runs/execution/mw_cross_indication_reference_release_gate_20260718/cms_w1_backend_implementation_round5.md`

Include exact changed files, exact commands/results, remaining risks, and a
compact loop trace. Finish implementation and tests before writing the report.
