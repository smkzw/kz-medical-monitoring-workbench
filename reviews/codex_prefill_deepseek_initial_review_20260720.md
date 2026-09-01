# Codex Initial Review: Production DeepSeek Prefill

Date: 2026-07-20
Status: revise before real-model acceptance

## Verified Improvements

- One bulk model call replaces field-by-field model calls.
- The direct product provider remains `deepseek-v4-pro`; no Codex/Hermes
  runtime dependency was introduced into the product path.
- Deterministic prefill is generated before AI enrichment and remains
  available after provider failure.
- The external model call now occurs before `BEGIN IMMEDIATE`; the subsequent
  transaction rechecks the persisted revision before commit.
- The API endpoint creates the prefill AI adapter from the existing direct
  provider configuration.

## P0/P1 Findings To Resolve

### 1. AI write scope is broader than the prompt claims

`_AI_ELIGIBLE_FIELDS` currently equals all
`SUPPORTED_STUDY_DEFINITION_PATHS`. The structured payload therefore advertises
identity and confirmed fields such as protocol ID, version, indication, study
phase, investigational product and target mechanism, although the system prompt
only intends condition term, title, population, design pattern and intervention
summary.

Required correction: define an explicit minimal allowlist. The parser must
reject every field outside that allowlist even when the model returns it.

### 2. Exact-fact blocking is path-only, not content-aware

The current parser skips five dedicated exact-fact paths, but accepts arbitrary
strings under broad fields such as `picos.intervention_summary`,
`framing.population_intent` and `framing.design_pattern`. A model can therefore
place unsupported dose, schedule, washout, threshold, endpoint, sample-size or
AESI facts inside an allowed free-text field.

Required correction: either:

- require direct registered evidence IDs for every candidate containing an
  exact fact; or
- reject/quarantine exact-fact-like AI text into a blocked suggestion until
  source evidence is available.

Prompt-only prohibition is not an enforcement boundary.

### 3. AI output is mislabeled as study-definition evidence

Generic AI suggestions currently receive:

- `source_kind="study_definition"`
- `source_id="ai_bulk_prefill"`
- `source_text=<AI generated text>`

This presents generated content as if it were evidence from the StudyDefinition
and makes the candidate its own evidence.

Required correction:

- AI generation provenance must use `source_kind="other"` (or a dedicated
  future enum), with an AI provenance locator;
- actual evidence refs may only point to registered input source IDs or current
  StudyDefinition facts actually supplied to the model;
- generated candidate text is not an evidence quote.

### 4. Adopting an English condition term leaves the old search plan active

The project search plan is built during project creation, commonly from the
Chinese indication. Adopting
`framing.clinicaltrials_condition_term` updates framing and invalidation labels
but does not rebuild `search_plan.registry_filter`. The next competitor search
can still use the old Chinese condition term.

Required correction: adoption of any search-contract input must atomically
rebuild the versioned search plan or fail closed until regeneration. The
frontend must receive the new plan ID/revision.

### 5. Registry hints are not relevance-screened

The bulk prompt copies the first five snapshot titles without checking whether
the registry `conditions`, phase, study type, sponsor, product/target or public
documents are relevant. ClinicalTrials.gov `query.cond` performs semantic
expansion; a correct RA condition query can return non-RA studies on the first
page.

Required correction: use structured candidate facts, apply deterministic
minimum relevance gates, and let the model rank only the surviving candidates.
An HTTP success or nonzero `totalCount` is not a relevance success.

## Acceptance Tests Needed

1. AI attempt to change indication/product/phase/protocol identity is ignored.
2. Dose or numeric endpoint hidden inside an allowed free-text field is blocked
   without direct source IDs.
3. AI-generated prose is never serialized as `study_definition` evidence.
4. Condition-term adoption rebuilds the search plan and changes its plan ID.
5. RA semantic-expansion false positives do not become preferred evidence.
6. PNH exact-condition Protocol/SAP candidates survive relevance filtering.
7. Wrong model, timeout, invalid JSON and partial JSON retain deterministic
   output and auditable diagnostics.
