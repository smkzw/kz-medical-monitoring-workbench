# Codex Review: Production Prefill AI Tests

Date: 2026-07-20
Scope: `tests/test_medical_writing_authoring_prefill_ai.py`
Status: remediation required before acceptance

## P0 - Unknown evidence is accepted instead of rejected

`test_unknown_source_ids_do_not_corrupt_known_sources` injects
`fabricated_source_xyz` and passes when the resulting candidate merely retains
an evidence reference. This proves the opposite of the required contract.

`test_ai_adapter_assigns_known_source_id_to_candidates` then treats
`ai_bulk_prefill` as a known source although it is neither a StudyDefinition
field nor a registered artifact/snapshot source. AI generation provenance
cannot be represented as source evidence, and generated text cannot be its own
evidence.

Required remediation:

- Assert that fabricated and unregistered source IDs are rejected or stripped.
- Assert that AI-only wording is marked as AI provenance/limitation without
  creating a false StudyDefinition/source artifact.
- Preserve real input evidence only, with source text that is the original
  input rather than the AI output.

## P0 - Exact-fact leakage through free text is not tested

The tests only submit suggestions under explicit exact-fact field paths such as
`picos.intervention_dose_regimen`. They do not test the actual failure mode:
unsupported dose, endpoint, timing, threshold, sample size, AESI or washout
facts embedded in otherwise eligible free-text fields such as
`picos.intervention_summary` or `picos.population_summary`.

Required remediation:

- Parameterize exact-fact leakage examples across every critical category.
- Prove the candidate is rejected/quarantined without direct registered source
  IDs.
- Prove an evidence-backed exact fact is accepted only when the supplied
  source ID is in the request's allowed source set.

## P1 - Bulk-call test exercises the wrong adapter layer

`BulkProviderCallTests` counts calls to the deterministic
`PrefillRankingAdapter`, which is intentionally invoked per field. It does not
prove that `DeepSeekPrefillAdapter.enrich_package()` makes exactly one provider
call for the complete package.

Required remediation:

- Use a counting provider and call `enrich_package()` once.
- Assert `provider.run` is called exactly once and the payload includes all
  eligible field groups.

## P1 - Transaction-order assertion is indirect

`test_generate_prefill_opens_transaction_after_inference` defines tracking
objects but never patches the service connection. It only proves that an
adapter ran and one revision was persisted; it does not prove inference
preceded `BEGIN IMMEDIATE`.

Required remediation:

- Instrument the actual connection/transaction boundary or use an enricher
  that asserts no write transaction is active when called.
- Preserve the separate failure-before-write test.

## P1 - Search-plan propagation is absent

No test proves that adopting
`framing.clinicaltrials_condition_term = Rheumatoid Arthritis` creates a new
versioned search plan whose `registry_filter.condition_term` replaces the old
Chinese term. This was a confirmed integration defect.

Required remediation:

- Generate, adopt the English candidate, reload, and assert a new plan ID and
  higher plan revision.
- Assert the active registry filter uses the adopted English term and the old
  snapshot binding is cleared.

## P1 - Registry-hint relevance is absent

No test proves that model hints exclude wrong-condition trials, wrong phase,
wrong study type or trials without public Protocol/SAP.

Required remediation:

- Build a mixed snapshot and assert only structured-condition/phase/type
  relevant candidates with public Protocol/SAP enter the bulk request.
- Include RA and PNH fixtures with both relevant and misleading records.

## P2 - Passing count overstates useful coverage

Several tests restate constants or Pydantic behavior rather than the production
contract. These may remain as low-cost checks but cannot substitute for the
missing integration assertions above. Acceptance is based on failure-mode
coverage, not the number of test functions.
