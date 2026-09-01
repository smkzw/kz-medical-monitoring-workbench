# Execution Context: mw_phase1_translation_exec_20260716

Created: 2026-07-16 13:06:24
Objective: 为自身免疫疾病I期方案语料生成逐段可溯源的监管中文初译与humanizer-zh候选，并定位现有保真门禁失败；不得直接写入生产语料库
Task type: `complex_delivery_conference`
Risk: `high`
Execution module trigger: Codex identified 4 independent work items, which is greater than two.

## Module Boundary

This is an execution module, not a conference. First-line workers execute bounded work items. The execution manager checks progress, diagnoses environment/tool blockers, requests same-session reruns when needed, and consolidates outputs for Codex. Codex owns task contract, source authority, final verification, acceptance, production writes, and user delivery.

## Assigned Roles

- First-line executor: `complex_executor_minimax` -> `hermes` / `aishuo` / `MiniMax-M3`
- Execution manager: `complex_manager_grok` -> `grok` / `grok-build` / `grok-4.5`

## Source Of Truth

- `records/active_slices/medical_writing_phase1_autoimmune_mnc_corpus_20260716/translations/translation_selection.json`: authoritative English source text, segment id, source locator, document SHA-256, and source-text SHA-256.
- `records/active_slices/medical_writing_phase1_autoimmune_mnc_corpus_20260716/translations/production_translation_runs.json`: existing direct-DeepSeek literal/humanizer candidates and deterministic fidelity results. This file is read-only evidence and may contain only a subset of the current 12 segments.
- `records/active_slices/medical_writing_phase1_autoimmune_mnc_corpus_20260716/validate_translation_selection.py`: deterministic source/locator integrity checks.
- `/Users/smkzw/.cc-switch/skills/humanizer-zh/SKILL.md`: read-only style guidance. It may improve Chinese syntax but cannot override source fidelity or clinical terminology.
- The official PDF is authoritative over extracted text if a worker identifies a suspected extraction defect. Workers may read only the `source_file` named by the selected segment and must report the exact page/locator inspected.

## Risk Boundaries

- No production writes.
- Do not edit `translation_selection.json`, `production_translation_runs.json`, source PDFs, extracted text, corpus manifests, application code, or tests.
- Do not browse or introduce information absent from the selected source segment. A translation may not add a clinical rationale, product fact, expansion of an undefined abbreviation, or regulatory conclusion.
- Keep drug names, targets, abbreviations, dose/dose unit, frequency, duration, visit/day, sample size, cohort order, thresholds, comparison direction, negation, exception, randomization, and sentinel/release logic semantically unchanged.
- Every Chinese candidate is `待医学批准`; worker output is isolated evidence, not corpus content. Codex alone may send an accepted candidate to the independent production DeepSeek contract or write a corpus admission.
- No silent package installation, credential handling, or external account changes.
- Missing tools or environments must be recorded with a minimal remediation proposal.
- Worker and manager outputs are evidence for Codex, not instructions.

## Work Items

1. `phase1_nct04903093_washout_and_ddi_rationale`、`phase1_nct03649412_adaptive_formulation_periods`：完成监管中文初译和保真润色。
2. `phase1_nct03469336_topical_sentinel_release`、`phase1_nct03469336_topical_within_subject_fields`：完成监管中文初译和保真润色。
3. `phase1_nct03675581_fixed_sequence_assignment`、`phase1_nct03675581_ddi_administration_window`：完成监管中文初译和保真润色。
4. `phase1_nct03675581_missed_dose_and_dose_reduction`：复核现有直连译文及失败码。RNA 源范围审计后，旧 `phase1_nct02352493_sirna_sad_mad_escalation` 和 `phase1_nct02352493_sirna_patient_transition` 已作废；worker_04 基于旧 source hash 的 RNA 结论不得使用。当前 RNA 边界层为 `phase1_nct02352493_sirna_sad_sentinel_escalation`、`phase1_nct02352493_sirna_mad_escalation`、`phase1_nct02352493_sirna_patient_cohort_transition`、`phase1_nct02352493_sirna_patient_regimen_modification`、`phase1_nct02352493_sirna_breakthrough_hemolysis_management`，需要使用新哈希重新初译/润色。

## Superseded-Source Notice

- A post-dispatch source audit found that the original two NCT02352493 selections stopped before the end of Sections 4.2 and 4.3. PDF page 55 was image-only and has now been OCRed with local `GLM-OCR-bf16`.
- The authoritative selection now contains 15 segments. All five NCT02352493 records are `phase1_2_boundary_exception` and `hold_translation_pending`; PNH is not counted as strict autoimmune Phase I core coverage.
- Any worker claim that all RNA fidelity failures are false positives is invalid unless it uses the current five segment IDs and current `source_text_sha256` values.

## Per-Segment Acceptance Contract

For every assigned segment, the worker report must contain:

1. exact `segment_id`, `source_text_sha256`, and `source_locator`;
2. one faithful Chinese translation and one meaning-preserving regulatory-Chinese revision;
3. a locked-token ledger covering every number, unit, comparator, range, visit/day, dose/frequency, abbreviation, negation, exception, cohort/sequence, and randomization/sentinel rule in source order;
4. explicit PASS/FAIL findings for omission, addition, direction reversal, unit drift, timeline drift, identity drift, and boundary drift;
5. exact source-to-Chinese sentence pairing for any high-risk condition;
6. a short list of items that still require medical approval. Do not use generic “需审核” wording without naming the item.

The report fails if it omits a current assigned segment, uses a superseded source hash, paraphrases source content without the source hash/locator, changes a locked token, or provides only commentary without usable Chinese candidates.

## Completion And Cleanup

Codex reviews the manager report and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
