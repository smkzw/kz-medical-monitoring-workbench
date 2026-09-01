# Medical Writing Pre-PICOS Evidence Loop P0

Updated: 2026-07-20  
Owner: Codex architecture and final acceptance  
Status: architecture accepted; implement in the active competitor-triage causal
chain after its current pass returns

## User Outcome

After the user supplies only the investigational product, indication and study
phase, the product must be able to search ClinicalTrials.gov, let product AI
recommend a competitor Protocol/SAP basket, download/parse/translate the
confirmed basket, and use the resulting source spans to prefill framing and
PICOS. The user mainly reviews, changes and confirms; the product must not ask
the user to write PICOS from a blank form.

## Reproduced Circular Dependency

1. `build_competitor_search_request()` correctly allows search from the
   three-field creation minimum.
2. The current DeepSeek prefill call happens before public Protocol/SAP content
   is downloaded and therefore cannot safely generate exact competitor regimen,
   endpoint, eligibility or visit facts.
3. `finalize_corpus_triage()` currently requires `picos_complete`.
4. `WritingReferencePreparationBatchService._frozen_scope()` currently requires
   finalized journey `corpus_triage`.
5. Therefore public source preparation cannot normally occur until after PICOS,
   while the user requires those sources to help generate PICOS.

## Required State Separation

### 1. Discovery basket confirmation

Meaning: the medical manager accepts the product-AI recommendation of which
public competitor Protocol/SAP documents should be prepared for design
research.

- Authoritative in `writing_reference.sqlite3`.
- Atomically records the basket and all relevance decisions.
- Can occur before `picos_complete`.
- Directly permits deterministic document preparation.
- Is not final corpus admission and is not a second medical approval workflow.

### 2. Evidence-grounded design proposal

Meaning: after preparation and translation, direct product DeepSeek
`deepseek-v4-pro` proposes structured design candidates from registered source
spans.

- Separate service/prompt from the creation-minimum prefill adapter.
- Inputs: current material study facts, confirmed basket, current source
  artifact/revision/translation hashes, and bounded source spans.
- Outputs: 3-5 materially distinct candidates where useful, including
  structured randomization, blinding, comparator regimen, background therapy,
  eligibility, endpoints, visits, interim analysis and Phase I parts.
- Exact facts require source-span IDs and locators.
- No model-created NCT, source, dose, endpoint or timing claim.
- User adoption updates the existing StudyDefinition through current typed
  adoption/impact-preview paths.

### 3. Final writing-corpus projection

Meaning: the now-confirmed PICOS and prepared sources form the traceable corpus
used for chapter drafting.

- May retain the journey `corpus_triage`/corpus-gate concepts.
- Carries the discovery-basket confirmation ID/hash.
- Re-evaluates alignment/staleness when StudyDefinition or source revisions
  change.
- Must not ask the user to approve the same source basket again.

## Codex Architecture Decision

The discovery basket is a separate authority and must not overload
`corpus_triage=finalized` or introduce a polymorphic meaning for "finalized".

- `writing_reference.sqlite3` owns the authoritative basket confirmation,
  selected/excluded relevance decisions, confirmation hash and projection
  recovery state.
- The authoring journey may store a derived
  `discovery_basket_projection` reference, but that reference does not imply
  that PICOS or the writing corpus is final.
- The preparation batch reads the current authoritative confirmation directly
  and may start before PICOS.
- When PICOS becomes complete, the journey idempotently projects the same
  confirmation into the final writing corpus without a second user action.
- Cross-database writes are never described as atomic. The authoritative
  reference transaction commits first; journey projection is replayable and
  may remain `projection_pending`.

This keeps four distinct meanings:

1. `basket_confirmed`: the user accepted the AI-recommended research-source set.
2. `sources_prepared`: the selected public documents were downloaded, parsed,
   content-validated and, where required, translated/QC'd.
3. `design_adopted`: the user selected or edited evidence-grounded structured
   design candidates.
4. `corpus_projected`: PICOS is complete and the confirmed sources are admitted
   to the chapter-writing corpus.

The product must use decision wording rather than approval wording. A medical
manager's selection is already the medical decision; no subsequent generic
"待医学批准" state is allowed for the same action.

## Minimum Product Changes

1. Make preparation-batch scope accept an authoritative, current competitor
   discovery confirmation from the reference database before PICOS completion.
2. Preserve compatibility with existing finalized journey triage.
3. Add an evidence-grounded structured-design proposal run after source
   preparation/translation.
4. Keep the creation-minimum prefill lightweight and non-exact; do not simply
   add exact design fields to its AI allowlist.
5. Project the confirmed discovery basket to final journey corpus state when
   PICOS becomes complete, idempotently and without a second approval.
6. Expose progress as:
   `检索研究 -> AI筛选 -> 已确认来源 -> 下载/解析 -> 翻译/质控 ->
   生成设计建议 -> 待用户修订确认`.
7. After a content-validation override, automatically and idempotently
   reconcile the corresponding `review_required` preparation item to
   `prepared` when the repository confirms `user_overridden`; do not require a
   hidden manual retry or rebuild the existing override endpoint.
8. Add an evidence-design proposal service separate from the initial prefill
   adapter. It must bind each exact fact to a registered source span and block
   adoption when source revisions or the StudyDefinition state hash change.

## Acceptance

- From a fresh project containing only drug, indication and phase, a real
  product-AI run reaches prepared/translated public Protocol/SAP evidence before
  PICOS is complete.
- A structured active-comparator candidate can carry source-backed product,
  dose/frequency, route and treatment period into the sole IP regimen authority.
- Background treatment remains structured non-IP `BACKGROUND`; CM, rescue and
  dose adjustment remain separate.
- Exact eligibility, endpoint and timing facts contain registered source span
  IDs and locators.
- The user approves the discovery basket once and later confirms design choices;
  no duplicate “医学批准” action appears.
- Change of source revision or material creation facts marks the design proposal
  stale and blocks blind adoption.
- The end-to-end typed state path is observable as:
  `search_executed -> triage_running -> triage_review_ready ->
  basket_confirmed -> preparation_running -> preparation_complete ->
  translation_running -> translation_complete ->
  design_proposal_generating -> design_proposal_ready -> design_adopted ->
  picos_complete -> corpus_projected -> writing_ready`.
- A preparation or journey projection failure is recoverable without asking
  the medical manager to approve the basket again.
