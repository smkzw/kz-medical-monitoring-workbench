# Medical Writing Translation Alignment V11 Worker

You are Hermes / aishuo / cms-model, the first-line implementation worker for
one bounded production-code remediation. Read `/Users/smkzw/.hermes/SOUL.md`,
`/Users/smkzw/.codex/AGENTS.md`, and the closest project `AGENTS.md` in full
before acting. Codex remains the final source, clinical, regulatory and release
authority.

## Objective

Make the existing mandatory pipeline

`Flash document plan -> Hy-MT2 body translation -> Flash integration/QC ->
deterministic fidelity -> medical review`

produce auditable one-to-one source/target translation units for dense protocol
tables, lists, eligibility criteria and prose. The repair must prevent omission,
merging, reordering and category narrowing without weakening any current
scientific or regulatory gate.

Do not run ClinicalTrials.gov, production DeepSeek, oMLX, the stable 5174/8911
services or any real project in this pass. Codex will run the real AD v11 probe
after deterministic source/test acceptance.

## Primary evidence

Read these files only:

- `records/active_slices/medical_writing_cross_indication_reference_gate_20260718/TASK_RECORD.md`
- `context/mw_ad_translation_fidelity_review_20260718_conference_context.md`
- `runs/conference/mw_ad_translation_fidelity_review_20260718/general_chair_grok45.md`
- `runs/execution/mw_cross_indication_reference_release_gate_20260718/cross_indication_e2e_run_v10/AD/translation_fidelity_evidence.json`
- `services/api/app/chapter_translation_pipeline.py`
- `services/api/app/main.py`
- `services/api/app/writing_reference.py`
- `services/api/app/writing_reference_translation_batch.py`
- `services/api/app/writing_reference_repository.py`
- `services/api/app/regulatory_translation_glossary.py`
- `services/api/assets/medical_writing_glossary/regulatory_translation_glossary_v1.json`
- `tests/test_document_pipeline_round8.py`
- `tests/test_mw_round3_backend_remediation.py`
- `tests/test_writing_reference.py`

The initial list is not a blanket prohibition on adjacent reads. Record each
additional source read and why it was needed.

## Codex-verified observations

1. AD ch07 current 6032-character Hy-MT2 chunk retained only 28/45 bullets;
   the next retained 50/61. The final chapter lost 28 of 114 bullets and many
   Week 16 facts.
2. A production Hy-MT2 probe with about 3000 source characters, strict
   no-summary wording and 17 stable source-unit markers returned all 17 markers
   exactly once and in order. It retained all 35/35 bullets and
   `finish_reason=stop`.
3. Production DeepSeek Flash preserved those same 17 markers exactly.
4. Injecting the actual locked glossary (`estimand -> 估计目标`,
   `intercurrent event -> 伴发事件`) and only clinical abbreviations detected by
   the product regex made that probe pass current number/unit/comparator/
   controlled-term fidelity. A broad title-case list produced bad Chinese
   such as `Trial试验`; never use generic capitalization as abbreviation logic.
5. A population probe proved line-level IDs alone are insufficient: one long
   source line still lost citation `(62)` and generic `TCI`. Translation units
   therefore need bounded semantic splitting inside long lines, plus per-unit
   deterministic checks and one bounded correction pass.
6. Current real defects that must remain blocking until corrected:
   TCI category narrowed to tacrolimus ointment, `at least 28 days` weakened to
   fixed `28 days`, `4 weeks` changed to `4天`, and `evaluation of the IMP`
   narrowed to `疗效评估`.
7. Do not implement `soft_blocked`. Do not accept model self-reported
   `passed=true` without deterministic checks.

## Required implementation

### 1. Translation-unit contract

- Add deterministic helpers in `chapter_translation_pipeline.py` (or the
  smallest existing adjacent module) that:
  - split source text into ordered nonempty semantic units;
  - preserve paragraph/list/table-row boundaries;
  - further split long lines at safe sentence, bullet and numbered-criterion
    boundaries, without splitting decimal numbers, abbreviations or comparator
    expressions;
  - use a bounded unit size suitable for protocol clauses;
  - render stable ASCII unit IDs such as `[[CMS_SEG_0001]]`;
  - parse a model response and require exactly the expected IDs, once each, in
    order, with nonempty target text;
  - reject missing, duplicate, reordered, unknown or empty units.
- The unit identity is deterministic from the source order and is re-derivable
  from stored source text. Never expose the markers in the admitted Chinese
  corpus or writing candidate.
- Reduce the default translation chunk target from 6000 to the real-probe
  supported 3000 characters. Preserve indivisible-unit and table-header
  behavior. Do not split an intact table row only to meet the target.

### 2. Hy-MT2 adapter

- Bump the Hy-MT2 prompt contract version.
- Send marked source units and separately labelled read-only context.
- Inject the actual matched glossary contract content, not a version label.
- Add only abbreviations detected by the product clinical-abbreviation pattern,
  including common mixed-case clinical forms such as `eCRF`, `eGFR`, `mITT`,
  `vIGA-AD`; do not preserve title-case ordinary English words.
- Require exact unit/cardinality/order preservation, exact numbers, citation
  markers, units, comparators, time windows, negation, endpoint hierarchy and
  abbreviations; forbid summarization, merging and category-to-product
  narrowing.
- Use a sufficient output cap for the smaller chunk and inspect
  `finish_reason`; truncated or malformed output fails closed.
- Perform at most one deterministic corrective Hy-MT2 retry for failed unit
  coverage/cardinality or a bounded set of unit-level deterministic fidelity
  findings. The retry must identify exact failing unit IDs and observed codes.
  A second failure stops and remains blocked; no unbounded loop.

### 3. Flash integration/QC adapter

- Bump the Flash integration prompt contract version.
- Build aligned marked source/target envelopes from the Hy-MT2 unit output.
- Require exact marker coverage/order and preserve table/list/numbered-clause
  cardinality. Parse and remove markers only after validation.
- Evaluate fidelity per aligned unit and across the final chapter. A legitimate
  `疗效` occurrence in one source unit must not mask an unsupported `疗效`
  addition in another unit.
- If the first Flash output fails deterministic aligned-unit checks, perform at
  most one corrective Flash pass with exact unit IDs/failure codes and the
  first output. If the second output fails, return a blocking result.
- Preserve the existing rule that malformed JSON, empty integrated text,
  provider failure or model `passed=false` fails closed.

### 4. Deterministic fidelity precision

- Add an aligned-unit fidelity result/helper with exact structural cardinality
  checks for markers, bullets, numbered criteria and table rows/cells when
  represented in the source.
- Keep citation identifiers such as `(62)` under preservation control. Do not
  globally discard citation numbers merely to remove a false positive; imported
  protocol references must later be reindexed.
- Fix only evidence-backed parser asymmetries with positive and negative tests:
  - en/em-dash ranges without surrounding spaces;
  - Chinese `满N年/月` as minimum-duration wording;
  - `>=2.0 x ULN` versus `≥正常值上限的2倍` word order;
  - mixed-case clinical abbreviations;
  - legitimate Chinese abbreviation equivalents, including non-specific IUS
    wording, without allowing TCI category narrowing.
- Retain blocking for omitted `至少`, changed week/day units, missing
  abbreviations/controlled terms, category narrowing and unsupported medical
  concepts.
- Do not blanket-delete or block Markdown table delimiters or `<br>` here.
  Table structure is a source feature that later must render as an editable
  table. Prevent raw markers from reaching the candidate, but do not flatten
  legitimate table structure into prose.

### 5. Identity and stale reuse

- Bump the composite translation contract version/hash.
- Ensure current document plan/chunk/integration/revision reuse cannot silently
  return v0.1/v0.2 translation output after the new Hy/Flash/alignment contract.
  Use an explicit downstream translation-contract fingerprint in the plan or
  integration identity rather than relying only on changed comments.
- Preserve immutable old rows and build new current lineage. Do not update or
  delete old plan/chunk/integration records.

## Required deterministic tests

Add behavior tests, not source-string assertions:

1. dense 114-bullet/estimand-style fixture chunks around 3000 and preserves all
   bullets and ordered source units;
2. long eligibility line splits before a new numbered criterion and around
   sentence/list boundaries without breaking `2.0`, `e.g.`, `>=`, `EASI-50`;
3. missing/duplicate/reordered/empty/unknown marker fails closed;
4. broad title-case words are not classified as abbreviations; eCRF/eGFR/mITT/
   vIGA-AD and existing uppercase clinical abbreviations are;
5. Hy response `finish_reason=length`, empty output or missing marker fails;
6. first compressed Hy output triggers one correction, corrected output
   continues; second bad output blocks and call count is exactly two;
7. Flash preserves markers, strips them from final Chinese and performs at most
   one corrective pass;
8. unit-level unsupported `疗效` addition is caught even when a different unit
   legitimately contains efficacy;
9. `(62)` omission, `at least 28 days` weakening, `4 weeks -> 4天`, TCI ->
   tacrolimus and comparator reversal remain blocked;
10. en-dash age range, `满12个月`, `2.0 x ULN` word order and accepted IUS
    equivalent pass, while nearby true defects still fail;
11. prompt/contract bump invalidates v10-style chunk/integration reuse without
    mutating immutable records;
12. direct translation and batch translation use the same new aligned contract.

Run the smallest focused tests first, then:

```bash
python3 -m pytest -q \
  tests/test_chapter_translation_pipeline.py \
  tests/test_document_pipeline_round8.py \
  tests/test_mw_round3_backend_remediation.py \
  tests/test_mw_round5_backend_contract.py \
  tests/test_writing_reference.py \
  tests/test_writing_reference_translation_service.py \
  tests/test_writing_reference_translation_batch.py
```

Then run all backend tests whose node IDs match
`writing_reference|chapter_translation`. Report exact counts and warnings.

## Hard boundaries

- No stable runtime/database/ports/credentials/real projects or public protocol
  files may be mutated.
- No external model, network, OCR or browser call in this worker pass.
- No paid/commercial dependency and no model replacement.
- No weakening, soft-blocking, automatic corpus admission or medical approval.
- Keep edits limited to the translation/alignment contract, exact precision
  fixes, directly necessary identity/repository logic and focused tests.
- Do not modify frontend in this pass.
- Do not claim clinical, regulatory, browser, DOCX or release acceptance.

Write exactly one output file:

`runs/execution/mw_translation_alignment_v11_20260718/cms_alignment_worker.md`

The report must list exact files changed, tests run/results, remaining risks and
a compact action/observation/evaluation/decision trace. Source and tests are the
deliverable; Codex will inspect and rerun them.
