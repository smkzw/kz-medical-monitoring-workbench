# Qoder Same-Session Remediation: AI-First Prefill Backend

Continue PID 39908 / qwen3.8-max-preview in the same Qoder session. This is a
targeted remediation of your prior implementation, not a new architecture
task. Read the current global `/Users/smkzw/.codex/AGENTS.md` first.

## Codex observed result

The established project interpreter is:

```bash
/usr/bin/python3 -m pytest
```

It has pytest and Pydantic 2 and runs the repository successfully. Your report
incorrectly treated the test environment as unavailable. Codex ran:

```bash
/usr/bin/python3 -m pytest -q tests/test_medical_writing_authoring_prefill.py
```

Actual result: `7 failed, 18 passed`.

Failures:

1. Six adoption tests fail because
   `MedicalWritingAuthoringJourney` has no `field_states`.
   The authoritative field states are
   `MedicalWritingStudyDefinition.field_states`.
2. `package_is_stale(package, updated)` is true immediately after generation.
   The fingerprint incorrectly includes the Journey revision that the generate
   operation itself increments.
3. `values_materially_distinct("随机、双盲", "随机 双盲")` returns true.
   Punctuation removal leaves a whitespace-only difference.

## Required remediation

### StudyDefinition authority

- Do not add `field_states` to `MedicalWritingAuthoringJourney`.
- Adoption must update `framing` and `picos` on both Journey and the single
  authoritative `MedicalWritingStudyDefinition`.
- Preserve unchanged StudyDefinition field states, imported synopsis/source
  evidence, manual edits, created_at, source artifact IDs, and study schema.
- For each adopted changed path, write a valid
  `MedicalWritingStudyFactState`: existing enum status `confirmed` is the
  project-fact confirmation state; set `value_origin=medical_manager_edit`,
  `reviewed_by/reviewed_at`, and `confirmed_by/confirmed_at`.
- Candidate state remains `user_confirmed`. Do not create an approval object or
  a second approval step.
- Record candidate/package provenance in the immutable journey event detail. If
  a typed optional source-candidate field is genuinely needed on
  `MedicalWritingStudyFactState`, add it additively and update validators/tests;
  do not persist an untyped dictionary that the Pydantic model drops.
- Recompute StudyDefinition revision, unresolved paths, deterministic synopsis,
  study-schema staleness, and `state_sha256` through existing builder/helpers or
  an equivalently safe narrow helper.

### Fingerprints and sequential adoption

- Generation must return a package that is not stale relative to the persisted
  post-generate Journey.
- Journey revision alone is not a source-fact fingerprint. Fingerprint framing,
  PICOS/StudyDefinition facts, search snapshot, corpus/source state, and the
  relevant source hashes.
- External relevant StudyDefinition/search/corpus changes must make the package
  stale.
- Medical managers must be able to adopt several independent fields from the
  same package sequentially. A successful controlled adoption may rebase the
  package to the resulting current input/revision while incrementing
  `package_revision`; it must still invalidate affected downstream artifacts.
  Do not solve immediate staleness by making the package unusable after the
  first adopted field.
- A stale external write or wrong expected Journey/package revision must still
  return a conflict.

### Canonicalization

- Punctuation-only and whitespace-only variants must deduplicate.
- Preserve material differences in structured values.

### Test corrections

- Update tests to assert the actual authority:
  `updated.study_definition.field_states[path].status == "confirmed"` and the
  adopted candidate state is `user_confirmed`.
- Do not weaken any of the 14 required behavioral scenarios.
- Add/retain an explicit sequential adoption test covering two independent
  fields from one package.
- Add a test proving an external framing/search/corpus change makes the package
  stale while the freshly persisted generated package is not stale.

## Verification

Run exactly:

```bash
/usr/bin/python3 -m pytest -q tests/test_medical_writing_authoring_prefill.py
/usr/bin/python3 -m pytest -q \
  tests/test_medical_writing_authoring_journey.py \
  tests/test_medical_writing_synopsis_import.py \
  tests/test_writing_reference_discovery_service.py \
  tests/test_writing_reference_api.py \
  tests/test_medical_writing_protocol_template.py
/usr/bin/python3 -m ruff check \
  packages/contracts/workbench_contracts/models.py \
  packages/contracts/workbench_contracts/__init__.py \
  services/api/app/medical_writing_authoring_journey.py \
  services/api/app/medical_writing_authoring_prefill.py \
  services/api/app/main.py \
  tests/test_medical_writing_authoring_prefill.py
```

Update `runs/qoder_authoring_prefill_backend_implementation_20260719.md` with
the observed failures, exact remediation rounds, exact passing output, and any
remaining risk. Do not claim completion from syntax checks.

Finish with the absolute report path and `DONE`.
