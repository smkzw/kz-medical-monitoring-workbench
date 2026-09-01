# R4-D06 implementation correction — same worker follow-up 7

Continue worker session `019ff7a9-93f2-7000-8500-c02c1a59c529`. The same independent verifier rejected followup6 for one narrow P1 runtime gap. Fix only that gap and prove it closed.

## Hard boundaries

- Work only in the current workspace.
- Writes only in `poc/medical_monitoring_ai_native_r4/src/mm_r4/`, its `tests/`, and `README.md` if documentation truly changes.
- Write exactly one output file: `runs/pi_medical_monitoring_r4_d06_implementation_20260813_followup7.md`. Runner-managed; return it, do not write through tools.
- Do not edit frozen artifacts/generator, R1-R3, product/UI/services, medical-writing, security, prompts/context/reviews/runs.
- No services/8911, real data/providers, installs, or unrelated cleanup.

Read these files only:

- `reviews/medical_monitoring_r4_d06_efficacy_slice_contract_v1_20260812.md`
- `runs/pi_medical_monitoring_r4_d06_implementation_20260813_followup6.md`
- `runs/codex-subagent_medical_monitoring_r4_d06_implementation_review_20260813_followup5.md`
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

Adjacent R1-R4 tests may only be executed for regressions.

## Starting snapshot

- evaluator `b41b68df85c08e6389dfb605b27eb0942cf62dad925201516be23df5b7c1b488`
- projection `12ef2eeec7159ed3b5d29966922894739c141df9ee8ebb61f9b33c53b8556da4`
- mutation tests `839f3d2a45ff0b8079e61a943cc4967eb438f61b298800d1a5b48bd3442b1349`
- frozen contract/catalog/oracle/registry/generator `460aba75…/d4774a82…/772bca08…/a02c4f8b…/fea1ad56…`, unchanged.

## Required correction

The verifier reproduced two hash-only mutations that still return the original positive medical result:

1. alter only `AcceptedD05AssessmentInventoryItem.hash`;
2. alter only `D05AssessmentForeignKey.hash`.

Before either typed object is consumed as authority, recompute its contract-defined content hash from its own typed fields and compare it to the embedded `hash`; mismatch must fail closed through the existing D06 contract-violation path. Do not key on fixture/case/test identity, oracle values, canonical literals, or hard-coded blobs. Preserve the already accepted four-way D05 semantic checks and the Journey serializer checks.

Add exact regression mutations for both escapes and any narrowly necessary adjacent hash mutation. Run the full 219 raw/oracle/DSL harness, mutation suite, focused/full R4 and R2/R3/R1 regressions, generator/hash checks, Ruff E/F, in-memory compile/import/export, port 8911, and task-created cache checks. Report final hashes and counts. Do not claim acceptance.
