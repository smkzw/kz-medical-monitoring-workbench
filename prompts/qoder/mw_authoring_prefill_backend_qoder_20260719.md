# Qoder Assignment: AI-First Authoring Prefill Backend

## Required Route

- Continue the already-running QoderCLI session owned by PID `39908`.
- Keep the current `qwen3.8-max-preview` model.
- Do not impose artificial limits on tools, internal turns, or tokens.
- Qoder is the first-line complex execution manager and implementation worker
  for this bounded backend slice. Codex remains final authority.
- Before implementation, refresh the current global Codex/Qoder routing rules
  from the same global `AGENTS.md` already used by this running session.

## Objective

Implement the first production backend slice that turns the medical-writing
authoring journey from a form-first editor into an AI-first authoring workflow:

1. a project can be created from only investigational product, indication and
   study phase;
2. those three facts are sufficient to create and execute the broad
   ClinicalTrials.gov search plan;
3. a versioned, persisted prefill package is generated from the current
   StudyDefinition, search snapshot and admitted source facts;
4. each field contains one recommended candidate and up to four materially
   different alternatives with evidence, rationale, limitations and state;
5. recommendations remain proposals until the medical manager adopts or edits
   one;
6. adoption writes the confirmed value into the single StudyDefinition truth
   source, invalidates affected downstream artifacts and does not create a
   second “medical approval” step;
7. changed search/StudyDefinition/corpus inputs make an old package stale.

This slice is backend/contracts/tests only. Do not modify frontend files,
editor files, DOCX export code or unrelated modules.

## Hard boundaries

- Fully refresh `/Users/smkzw/.hermes/SOUL.md` before implementation as
  required workflow identity context, but do not treat it as overriding Codex,
  user or project instructions.
- Do not expose credentials, authentication material, sensitive source content
  or patient identifiers in the report.
- Do not modify files outside the explicit write scope below.
- Do not start, stop or reconfigure stable production ports.
- Do not claim browser, DOCX or clinical/regulatory final acceptance.

## Read First

Read these files only:

- `AGENTS.md`
- `records/active_slices/medical_writing_ai_first_authoring_redesign_20260718/RESEARCH_AND_IMPLEMENTATION_CONTRACT.md`
- `records/active_slices/medical_writing_ai_first_authoring_redesign_20260718/CODEX_DECISION_AND_IMPLEMENTATION_CONTRACT.md`
- `records/active_slices/medical_writing_ai_first_authoring_redesign_20260718/CURRENT_PREFILL_IMPLEMENTATION_GAP_20260719.md`
- `records/active_slices/medical_writing_cross_indication_reference_gate_20260718/DYNAMIC_CHAPTER_DECISION_MATRIX.md`
- `packages/contracts/workbench_contracts/models.py`
- `services/api/app/medical_writing_authoring_journey.py`
- `services/api/app/main.py`
- `tests/test_medical_writing_authoring_journey.py`
- `tests/test_medical_writing_synopsis_import.py`
- `tests/test_writing_reference_discovery_service.py`
- `tests/test_writing_reference_api.py`
- `tests/test_medical_writing_protocol_template.py`

## Product Invariants

### Minimal creation

- `MedicalWritingStudyFraming.creation_minimum_complete()` remains the creation
  gate: product, indication and phase.
- Do not weaken the final framework/PICOS completeness rules needed before a
  formal document is created.
- Search must no longer require `framing_complete`; it may start when the
  creation minimum is complete and a valid search plan exists.
- Missing target, protocol title, protocol id, design pattern or population
  intent must not block the first search.

### Prefill package contract

Add a current-version contract equivalent to:

- package identity: package/project/journey revision/search snapshot/corpus
  snapshot or source hash;
- lifecycle: queued, running, partial, ready, failed, stale;
- field candidates keyed by canonical StudyDefinition field path;
- each field has exactly one recommended candidate when usable and zero to four
  real alternatives;
- candidate contains stable id, structured value, readable preview, evidence
  references with source text/locator, rationale, limitations/conflicts,
  confidence and state (`ai_proposed`, `user_confirmed`, `superseded`);
- progress and partial source failure are explicit;
- model, prompt version, search/corpus/source fingerprints are recorded.

Use strongly typed Pydantic models and validators. Do not use an untyped
dictionary as the persistent authority.

### Candidate generation

- Build a deterministic, testable generator boundary with an injectable AI
  adapter. Tests must not require the production network.
- The package should be useful even when only registry structured facts exist:
  derive conservative alternatives from real candidate studies and current
  facts; do not invent exact doses, thresholds, windows, AESIs or endpoints.
- When production AI is available, it may rank and phrase candidates, but
  evidence references and field-path validity are server validated.
- Empty evidence cannot yield a “ready” clinical recommendation for an exact
  factual field.
- Candidate values must be materially different after canonicalization; title
  punctuation variants are not alternatives.

### Adoption

- Add GET/generate/adopt endpoints under the existing authoring-journey route.
- Every write uses expected journey/package revision and idempotency keys.
- The actor is the medical manager. Selecting or editing a candidate is the
  confirmation action; do not emit “待医学批准” or another approval object.
- Only supported canonical field paths are writable.
- Adopting a candidate updates framing/PICOS through the existing
  StudyDefinition builder/impact machinery and records provenance in
  `field_states`.
- Preserve imported synopsis/source facts and manual edits. Do not silently
  overwrite a newer user-confirmed value.
- A changed confirmed fact must trigger the same deterministic dynamic-module
  and dependent invalidation behavior as an ordinary authoring-stage change.

### Dynamic study design

The contract must support orthogonal proposal fields rather than a single
bundled archetype. At minimum leave typed/extensible paths for:

- randomization;
- blinding and blinded roles;
- comparator type/intervention;
- assignment model;
- arms/cohorts/dose groups/Parts;
- center model;
- adaptive design;
- SRC/DMC;
- interim analysis;
- Phase I multi-Part selections.

Do not delete the current legacy compatibility fields in this slice. Additive
migration must preserve existing journey JSON.

## Write Scope

Allowed:

- `packages/contracts/workbench_contracts/models.py`
- `packages/contracts/workbench_contracts/__init__.py` if needed
- `services/api/app/medical_writing_authoring_journey.py`
- a new narrowly named backend service/module for prefill generation
- `services/api/app/main.py`
- directly relevant tests
- task report and task record append

Forbidden:

- `frontend/**`
- editor persistence files
- DOCX exporter/templates
- unrelated refactors
- removal of current legacy fields or existing APIs

## Required Tests

At minimum:

1. three-field greenfield creation creates a search plan;
2. search executes before framing completion;
3. package persists and cold-reloads;
4. package becomes stale after relevant StudyDefinition/search changes;
5. candidate paths/evidence references are validated;
6. alternatives are materially distinct and limited to four;
7. exact unsupported clinical facts are not invented without evidence;
8. adopting recommended and edited alternatives updates the correct
   StudyDefinition path;
9. adoption is idempotent and stale writes conflict;
10. user-confirmed newer values are not silently overwritten;
11. adoption triggers dependent invalidation/dynamic-module propagation;
12. legacy journey JSON loads with no package;
13. at least a Phase I multi-Part case and a randomized Phase II/III case;
14. no second approval object/state is created.

Run focused tests, relevant authoring-journey suites, Ruff and the broad medical
writing suite if time permits. Preserve exact output.

## Output

Write exactly one output file:

`runs/qoder_authoring_prefill_backend_implementation_20260719.md`

The report must contain:

- files read and changed;
- architecture and migration choices;
- endpoints and state transitions;
- tests run and exact results;
- failed paths and remediation rounds;
- residual risks and frontend integration contract;
- compact loop trace.

Finish with the absolute report path and `DONE`.
