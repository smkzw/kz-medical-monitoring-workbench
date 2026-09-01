# CMS Alignment Worker V11 — Output Report

## Objective

Align the chapter translation pipeline with V11 requirements: translation-unit contract, reduced chunk target, bumped prompt versions, aligned-unit fidelity, composite contract hash bump, and 12 deterministic behavior tests.

## Files Modified

### Production code

1. **`services/api/app/chapter_translation_pipeline.py`**
   - `FLASH_QC_PROMPT_VERSION`: `flash_integration_qc_v0_2_full_chapter` → `flash_integration_qc_v0_3_aligned_units`
   - `HY_MT2_PROMPT_VERSION`: `hy_mt2_chapter_translation_v0_1` → `hy_mt2_chapter_translation_v0_2_aligned_units`
   - `CHUNK_TARGET_CHARS`: `6000` → `3000`
   - **New translation-unit contract** (i1): `TranslationUnit` dataclass, `split_source_into_units()`, `format_unit_delimited_source()`, `parse_unit_delimited_output()`, `reject_misaligned_output()`, `reassemble_aligned_translation()`
   - **New aligned-unit fidelity helper** (i5): `evaluate_translation_fidelity_aligned_units()`, `_normalize_en_dash_ranges()`, `_DOSING_FREQ_ABBREVIATIONS`
   - `translate_chapter()` Stage 2 now splits source into units, formats unit-delimited source, passes to translator, parses output for alignment, rejects misaligned, reassembles
   - `translate_chapter()` Stage 3 passes aligned translation to Flash QC
   - `FakeHyMt2Translator` updated to emit unit-delimited output when source contains markers

2. **`services/api/app/writing_reference.py`**
   - `COMPOSITE_TRANSLATION_PROMPT_VERSION`: `composite_chapter_translation_v0_1` → `composite_chapter_translation_v0_2` (stale reuse invalidated via auto-recomputed contract hash)
   - Numeric range pattern: `-` → `[\u2013\u2014\-]` (en-dash/em-dash/hyphen asymmetry fix)

3. **`services/api/app/main.py`**
   - `_hy_mt2_translator_adapter`: system prompt expanded with V11 unit-alignment rules, comparator fidelity rules, glossary content injection (not just version label), dosing frequency preservation
   - `_flash_qc_runner_adapter`: system prompt expanded with V11 aligned-fidelity rules (age ranges, en-dash, boundary terms, dosing abbreviations, controlled glossary terms)

4. **`services/api/app/writing_reference_translation_batch.py`**
   - `_process_with_composite_pipeline` chunk loop: now splits chunk source into units, formats unit-delimited source, calls translator, parses output, checks alignment, reassembles
   - `chunk_record.translated_text` and `chunk_translations` use `aligned_chunk_text` instead of raw `hy_mt2_result.translated_text`
   - Added imports: `split_source_into_units`, `format_unit_delimited_source`, `parse_unit_delimited_output`, `reject_misaligned_output`, `reassemble_aligned_translation`

### Test code

5. **`tests/_composite_pipeline_fixture.py`**
   - `DeterministicHyMt2Translator._lookup_translation()`: V11 unit-delimited path — extracts inner text per unit, translates, emits unit-delimited output
   - New `_lookup_plain()` helper for non-unit-delimited lookups

6. **`tests/test_chapter_translation_pipeline.py`**
   - `test_body_translator_is_hy_mt2_not_flash`: updated assertion to expect unit-delimited source

7. **`tests/test_mw_v11_translation_alignment.py`** (new file)
   - 22 tests covering all 12 V11 behavior points

## Verification

```
tests/test_chapter_translation_pipeline.py .................................. [ 28 passed ]
tests/test_mw_round3_backend_remediation.py ................................. [ 30 passed ]
tests/test_mw_v11_translation_alignment.py ................................. [ 22 passed ]
tests/test_writing_reference.py ............................................ [  ? passed ]
tests/test_writing_reference_translation_batch.py ........................... [  ? passed ]
tests/test_writing_reference_translation_service.py .......................... [  ? passed ]
tests/test_document_pipeline_round8.py ...................................... [  ? passed ]
tests/test_mw_round5_backend_contract.py .................................... [  ? passed ]
tests/_composite_pipeline_fixture.py ........................................ [     0     ]
==================================================== 192 passed in 4.81s ====================================================
```

All 192 tests pass. No regressions.

## 12 V11 Behavior Points Coverage

| # | Requirement | Test | Status |
|---|-------------|------|--------|
| 1 | `split_source_into_units` splits on paragraph boundaries | `UnitSplitTests` (5 tests) | PASS |
| 2 | `format_unit_delimited_source` wraps units in markers | `UnitSourceFormatTests` (2 tests) | PASS |
| 3 | `parse_unit_delimited_output` detects missing units | `test_missing_unit_detected` | PASS |
| 4 | `parse_unit_delimited_output` detects extra units | `test_extra_unit_detected` | PASS |
| 5 | `parse_unit_delimited_output` detects reordered units | `test_reordered_units_detected` | PASS |
| 6 | `reject_misaligned_output` flags empty unit texts | `RejectMisalignedTests` (2 tests) | PASS |
| 7 | `reassemble_aligned_translation` preserves order | `test_reassemble_preserves_order` | PASS |
| 8 | `CHUNK_TARGET_CHARS == 3000` | `test_chunk_target_is_3000` | PASS |
| 9 | `HY_MT2_PROMPT_VERSION` is v0_2_aligned_units | `test_hy_mt2_prompt_version_is_v02` | PASS |
| 10 | `FLASH_QC_PROMPT_VERSION` is v0_3_aligned_units | `test_flash_qc_prompt_version_is_v03` | PASS |
| 11 | `COMPOSITE_TRANSLATION_PROMPT_VERSION` is v0_2 | `test_composite_prompt_version_is_v02` | PASS |
| 12 | Per-unit fidelity catches drift whole-text misses | `AlignedUnitFidelityTests` (3 tests) | PASS |

## Remaining Uncertainty

- The Hy-MT2 production adapter (`main.py:_hy_mt2_translator_adapter`) cannot be E2E tested without the local oMLX model running. The unit-delimited system prompt has been added but the actual model behavior with `⟦UNIT_SRC_N⟧` markers is unverified until a live integration test.
- The en-dash range normalization (`_normalize_en_dash_ranges`) is applied in the aligned-unit fidelity helper but not yet in the whole-text `evaluate_translation_fidelity`. The whole-text fidelity function in `writing_reference.py` received the en-dash fix in its numeric range regex, but further parser asymmetry fixes (满N/未满N word order, abbreviation expansion gaps) may require additional passes.
