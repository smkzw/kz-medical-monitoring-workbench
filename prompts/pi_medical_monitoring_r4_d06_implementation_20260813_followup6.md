# R4-D06 implementation correction — same worker follow-up 6

Continue worker session `019ff7a9-93f2-7000-8500-c02c1a59c529`. Same verifier followup4 rejected the current snapshot. Fix only the remaining correctable blockers and document the genuine frozen-authority limitation without inventing hard-coded authority.

## Hard boundaries

- Work only in current workspace.
- Writes only in `poc/medical_monitoring_ai_native_r4/src/mm_r4/`, its `tests/`, and `README.md`.
- Write exactly one output file: `runs/pi_medical_monitoring_r4_d06_implementation_20260813_followup6.md`. Runner-managed; return it, do not write through tools.
- Do not edit frozen artifacts/generator, R1-R3, product/UI/services, medical-writing, security, prompts/context/reviews/runs.
- No services/8911, real data/providers, installs.

Read these files only:

- `reviews/medical_monitoring_r4_d06_efficacy_slice_contract_v1_20260812.md`
- `runs/codex-subagent_medical_monitoring_r4_d06_implementation_review_20260813_followup4.md`
- `runs/pi_medical_monitoring_r4_d06_implementation_20260813_followup5.md`
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

## Starting snapshot

Evaluator `243952483bf45d6f9342a3ccb8b08d3d98e7070c2349a7c54698ce4cc882ef23`; projection `13e3fb3b627ed5c3f0b9a8ea6298834de0885357b46fc3d64702fd7ffc88d30c`; mutations `f63547256abd5d42232288add72532b30b37a2c02cd674d923ce7878422dee34`. Frozen five anchors unchanged.

## Required fixes

1. Reproduce verifier's rehashed D05 mutations and make each fail closed through cross-authority comparison: D05 unit/activity IDs, occurrence/timing dispositions, assignment, foreign-key producer payload/time, accepted assessment stable key/recall/time/locator, and assessment item value/locator/content. Validate every consumed assessment and item bidirectionally across `D05AssessmentBindingRef`, accepted inventory, foreign-key registry, shared spine, definitions, assessment-items and accepted result sources. Do not accept self-rehashed objects as their own authority.
2. Harden `journey_audience_payload_from_projection` itself: before serialization, verify each marker's locator/payload-hash/content-address relation and projection hash/identity consistency from its typed fields. A dataclass-replaced/mutated projection with changed locator or marker content but stale hash must raise a specific projection/contract error; a valid projection still serializes to the frozen unchanged payload, so the 219 oracle need not change. Add exact direct-serializer mutation tests.
3. If a consumed field has no independent authority anywhere in the frozen fixture, do not fabricate one. Enumerate exact field/path and explain why current contract either permits opaque stable identifiers under bidirectional relationships or requires a controlled erratum. Runtime fixes must not key on case/test identity or canonical fixture literals.

Add exact mutation tests for every verifier escape. Run 219 raw/DSL, mutation, full R4/R2/R3/R1, generator/hashes, Ruff E/F, compile/import/export, 8911/cache. Return hashes/counts and residual authority decision. Do not claim acceptance.
