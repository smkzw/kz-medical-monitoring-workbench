# Qoder Assignment: Protocol Structure Corpus Manager And Conference Chair

## Required Route

- Use the already-running QoderCLI process PID `39908`.
- Model must be `qwen3.8-max-preview`.
- Do not impose artificial limits on tool use, internal turns, or tokens.
- This assignment replaces the Grok Build execution-manager and conference-chair
  roles for this task. Grok Build is fallback only.

## Objective

Act as both:

1. execution manager for the three independent ClinicalTrials.gov Protocol
   candidate work items; and
2. sub-venue chair synthesizing the two independent conference participant
   reviews.

Codex remains final authority for source verification, clinical/regulatory
conclusions, production writes, browser/Word acceptance, and user delivery.

## Read First

- `/Users/smkzw/.codex/AGENTS.md`
- `AGENTS.md`
- `context/mw_protocol_structure_corpus_20260719_context.md`
- `context/mw_protocol_structure_corpus_exec_20260719_execution_context.md`
- `context/mw_protocol_structure_corpus_conf_20260719_conference_context.md`
- `plans/codex_main_venue_mw_protocol_structure_corpus_conf_20260719.md`
- `records/active_slices/medical_writing_cross_indication_reference_gate_20260718/TEMPLATE_AUTHORITY_MATRIX.md`
- `records/active_slices/medical_writing_cross_indication_reference_gate_20260718/DYNAMIC_CHAPTER_DECISION_MATRIX.md`
- `runs/conference/mw_protocol_structure_corpus_conf_20260719/general_aishuo_cms.md`
- `runs/conference/mw_protocol_structure_corpus_conf_20260719/general_opencode_deepseek_flash.md`
- when substantive: `runs/execution/mw_protocol_structure_corpus_exec_20260719/worker_01.md`
- when substantive: `runs/execution/mw_protocol_structure_corpus_exec_20260719/worker_02.md`
- when substantive: `runs/execution/mw_protocol_structure_corpus_exec_20260719/worker_03.md`

## Work

1. Independently test the sampling logic against the official
   ClinicalTrials.gov API and ProvidedDocs metadata. Do not accept publications,
   SAPs, registry summaries, duplicate sponsors, or multiple versions as
   separate Protocol samples.
2. Review each worker's indication/phase candidate set for sponsor diversity,
   exact phase classification, Protocol role, version choice, retrieval
   completeness, and likely edge cases.
3. Reconcile the two conference participant reports. Preserve disagreements and
   decide which claims require Codex verification rather than model consensus.
4. Produce a practical chapter-function ontology and a classification method
   that compares real medical/regulatory function rather than title strings.
5. Define how sample evidence may inform stable core, phase core, design-driven
   optional, indication-driven optional, explicit not-applicable, and
   insufficient-evidence states without misrepresenting frequency as regulation.
6. Specify controlled propagation to template nodes, corpus labels, evidence
   filters, AI candidate routing, tests, and migration.
7. Identify flaws or blind spots in the existing matrices and current task plan.
8. Do not edit production source code, templates, corpus admission state, or
   clinical content.

## Output

Write one detailed report to:

`runs/qoder/mw_protocol_structure_corpus_qoder_manager_chair_20260719.md`

The report must include:

- route identity, PID/model confirmation, sources and tools actually used;
- execution review by work item;
- candidate-set gaps and exact follow-up actions;
- participant agreements and disagreements;
- chapter-function ontology and applicability decision method;
- product/data-contract/test implications;
- failed paths, uncertainty, and claims requiring Codex verification;
- a compact loop trace: sources read, rounds, observations, evidence,
  uncertainty, and recommended next action.

Do not overwrite runner-managed participant or fallback files.
