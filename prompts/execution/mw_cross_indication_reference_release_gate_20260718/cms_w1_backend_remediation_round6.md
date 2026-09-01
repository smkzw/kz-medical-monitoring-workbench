# CMS Backend Remediation Round 6

This is a fresh bounded implementation pass after the previous CMS continuation
ended with an event-loop/session failure. The source now contains useful partial
Round 5 edits. Treat the current source and Codex's fresh test output as truth;
do not restart the earlier migration and do not weaken assertions.

## Read these files only as the initial context

Before editing, reread:

- `/Users/smkzw/.hermes/SOUL.md`
- `/Users/smkzw/.codex/AGENTS.md`
- project `AGENTS.md`
- `records/active_slices/medical_writing_cross_indication_reference_gate_20260718/TASK_RECORD.md`
- current source and tests named below

## Current verified state

Codex ran:

`python3 -m pytest -q tests/test_mw_round3_backend_remediation.py tests/test_mw_round5_backend_contract.py tests/test_chapter_translation_pipeline.py tests/test_writing_reference_extraction.py tests/test_writing_reference_translation_service.py tests/test_writing_reference_translation_batch.py tests/test_writing_reference.py`

Actual result at 2026-07-18 14:45 CST:

- 133 passed
- 4 failed

Failures:

1. `test_fidelity_blocked_is_terminal_and_has_no_review_or_admission_side_effect`
   expects non-empty fidelity failure codes, but the composite batch path only
   persists Flash-QC codes and drops deterministic fidelity codes.
2. `test_get_projects_review_and_admission_without_mixing_generation_state`
   and
   `test_get_projects_the_current_revision_after_medical_return_and_revision`
   receive an empty `translation_id`. The composite batch path updates only the
   batch item and does not persist/link the translation revision that medical
   review and corpus admission require.
3. `test_idempotency_conflict_existing_reuse_and_legacy_contract_regeneration`
   expects two reusable current candidates but preview reports one. Diagnose
   the contract/current-candidate test against composite provenance and fix the
   production compatibility check or deterministic fixture as appropriate.
   Do not count a stale legacy candidate as current.

## Production contract to preserve

- The authoritative body path remains Flash document/chapter planning ->
  Hy-MT2 body translation -> Flash integration QC -> deterministic fidelity.
- A QC-passed result must have non-empty integrated text.
- The final persisted translated text/hash must be the Flash-integrated
  candidate, not raw Hy-MT2 text.
- Batch and direct translation must create the same kind of immutable
  `WritingReferenceTranslationRevision`, with real `translation_id`,
  `revision`, lineage, AI run/provenance, fidelity result and auditability.
- Medical review and corpus admission must operate on that persisted revision.
- Merge Flash-QC failure codes and deterministic fidelity failure codes without
  losing either; deduplicate deterministically.
- The explicit user instruction/medical-review return comment and the rendered
  source-matched glossary contract must reach the composite adapters in both
  direct and batch paths.
- Keep GLM-OCR-bf16, Hy-MT2, DeepSeek Flash, dual-channel OCR lineage, active
  OCR concurrency <=8, idempotency, retry and progress contracts unchanged.
- Do not reintroduce a Flash-only body fallback.

## Required work

1. Reproduce the four failures exactly.
2. Inspect the direct composite service path and reuse its translation revision
   persistence contract rather than inventing a parallel batch-only record.
3. Make the smallest production and fixture corrections.
4. Add focused assertions proving:
   - batch items link to a real persisted translation revision;
   - medical review and admission can consume it;
   - final text/hash equals the Flash-integrated candidate;
   - merged fidelity codes survive;
   - idempotent rerun does not duplicate a translation revision.
5. Run the exact seven-file command above until green.
6. Run the broader selection returned by:
   `rg --files tests | rg 'writing_reference|chapter_translation'`.
## Hard boundaries

- Do not touch frontend files, stable runtime, real clinical inputs,
  credentials, or the three-indication harness.
- Do not use Flash as the sole body translator.
- Do not replace GLM-OCR-bf16, Hy-MT2 or DeepSeek Flash.
- Do not claim final three-indication E2E or release acceptance.
- Finish implementation and tests before writing the report.

Write exactly one output file:
`runs/execution/mw_cross_indication_reference_release_gate_20260718/cms_w1_backend_implementation_round6.md`

The report must list exact files changed, exact commands and counts, remaining
risks, and a compact action/observation/evaluation/decision trace. Source and
tests are the deliverable; the report is evidence only.
