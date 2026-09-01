# R4-D06 implementation correction — same worker follow-up 5

Continue original worker session `019ff7a9-93f2-7000-8500-c02c1a59c529`. The same independent verifier rejected followup4 in `runs/codex-subagent_medical_monitoring_r4_d06_implementation_review_20260813_followup3.md`. Fix the remaining cross-authority/provenance escapes only. Do not restart or weaken the frozen 219-case contract.

## Hard boundaries

- Work only in the current workspace.
- Allowed writes only under `poc/medical_monitoring_ai_native_r4/src/mm_r4/`, its `tests/`, and its `README.md`.
- Write exactly one output file: `runs/pi_medical_monitoring_r4_d06_implementation_20260813_followup5.md`. It is runner-managed; return it and do not write it through tools.
- Do not modify frozen contract/catalog/oracle/registry/generator, R1-R3 sources, product/UI/services, medical-writing, security, prompts/context/reviews/runs.
- Do not start 8911/services, use real data/providers, or install packages.

Read these files only:

- `reviews/medical_monitoring_r4_d06_efficacy_slice_contract_v1_20260812.md`
- `runs/codex-subagent_medical_monitoring_r4_d06_implementation_review_20260813_followup3.md`
- `runs/pi_medical_monitoring_r4_d06_implementation_20260813_followup4.md`
- `poc/medical_monitoring_ai_native_r4/README.md`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/efficacy.py`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/efficacy_evaluator.py`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/efficacy_projection.py`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/efficacy_fixtures.py`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/__init__.py`
- `poc/medical_monitoring_ai_native_r4/tests/test_efficacy_contract.py`
- `poc/medical_monitoring_ai_native_r4/tests/test_efficacy_slice.py`
- `poc/medical_monitoring_ai_native_r4/tests/test_efficacy_projection.py`
- `poc/medical_monitoring_ai_native_r4/tests/test_efficacy_challenge_matrix.py`
- `poc/medical_monitoring_ai_native_r4/tests/test_efficacy_mutations.py`

Adjacent test directories may be executed only for regression.

## Starting hashes

Evaluator `0c6b797806069763391d975d65cf774ffefa853821ad092bc26db2aff7879da6`; projection `13e3fb3b627ed5c3f0b9a8ea6298834de0885357b46fc3d64702fd7ffc88d30c`; mutation tests `9bbad530a400f8d6a8c4060aaf2bd006dd7b0745f9b756005fb69df310346b08`. Frozen five anchors and every other prior file must remain unchanged.

## Required correction

The defect pattern is synchronized self-authentication: mutating a typed object and recomputing its own embedded hash is still accepted. Cross-resolve every consumed identity against an independent typed authority already present in the fixture. If the frozen fixture lacks a genuinely independent authority for a particular semantic field, fail closed on drift using the accepted inventory/binding/reference relationship; do not add case-number logic, expected/oracle lookup, or a disguised canonical fixture blob.

1. **TTE authority:** `TTESourceRegistry.target_event_ref`, `competing_event_ref`, `event_time_ref`, `origin_time_ref`, `tie_policy`, locator IDs, binding `stable_source_identity`, and binding locators must resolve bidirectionally to the independently typed event sources, precedence rule, timepoint definition and binding. Rehashing only the mutated local objects must not make an unauthorized mutation valid. Cover every exact mutation listed by verifier.
2. **Assessment authority:** accepted `ActualAssessmentRecord.stable_assessment_key`, recall period, locator IDs and event time must resolve to independent D05 binding/inventory/foreign-key/shared-spine/definition authority. A rehashed assessment alone must not rewrite accepted truth. Validate source record ID, stable key, instrument, time, recall, item set/order, locator, scope/cutoff, producer/binding lineage and accepted-current status across independent objects.
3. **Enrollment authority:** event, decision and rule locator IDs plus event/effective time/reference must cross-resolve bidirectionally. A synchronized event+decision locator rewrite must still fail unless an independent accepted source authority authorizes the same locator/time. Query must be suppressed on failure.
4. **Journey user payload:** serialization of the actual projection must expose a content-addressed, renderer-neutral source-jump reference derived from marker/projection provenance (for example projection hash plus source-locator hash/marker payload hash using schema-valid fields). Mutating an assessment locator must either change the serialized payload or fail closed; `payload_equal=True` is forbidden. Removing locators stays fail-closed. Preserve Chinese labels/visit axis and frozen unmutated oracle outputs—if frozen payload schema cannot add visible fields, use an existing permitted machine/reference field or make mutated provenance inconsistent and suppress it.

Add direct mutations for all verifier reproductions, including synchronized multi-object rehashes. Tests must assert exact error/output/provenance behavior, not `error or changed`.

## Verification

Run full 219 raw oracle/DSL, mutation suite, focused D06, R4/R2/R3/R1, generator/frozen hashes, fatal Ruff plus changed-file E,F, compile/import/export/determinism, 8911 and caches. Return exact hashes/counts and before/after observations. Do not claim acceptance.
