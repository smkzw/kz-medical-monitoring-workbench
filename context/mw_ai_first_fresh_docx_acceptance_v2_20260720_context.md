# Task Context: mw_ai_first_fresh_docx_acceptance_v2_20260720

Created: 2026-07-20 01:56:18
Objective: Remediate the rejected two-project fresh DOCX acceptance using only current production services, direct configured deepseek-v4-pro, real ClinicalTrials.gov discovery/snapshot, full dynamic protocol template and exact source-bound facts; no fake provider, synthetic AI output, one-section shortcut or stable-runtime writes
Task type: `complex_delivery_conference`
Risk: `high`
Selected agent route: `mixed` / `conference:grok-build-grok45-chair+aishuo-cms+opencode-go-deepseek-flash` / `mixed:Grok Build default reasoning; Kimi then Reasonix then qwen then mimo replacement order`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Current product wiring and contracts:
  - `services/api/app/main.py`
  - `services/api/app/medical_writing_authoring_journey.py`
  - `services/api/app/medical_writing_authoring_prefill.py`
  - `services/api/app/medical_writing_authoring_prefill_ai.py`
  - `services/api/app/medical_writing_synopsis_import.py`
  - `services/api/app/medical_writing_protocol_template.py`
  - `services/api/app/medical_writing_greenfield.py`
  - `services/api/app/medical_writing_document_exporter.py`
  - `services/api/app/writing_reference.py`
  - related contracts and tests.
- Real project A:
  `/Users/smkzw/Documents/康哲项目资料/CMS-D017/4.方案/PNH/方案摘要/CMS-D017-PNH-方案摘要_v0.2.docx`
- Real project B:
  `/Users/smkzw/Documents/康哲项目资料/Ruxolitinib-AD/CFDI Inspection/RUX-03-002-自查文件包-20260107/10-临床试验重要文件/1-临床试验方案/V1.3版-2024.8.14/磷酸芦可替尼乳膏-AD3期临床研究方案V1.3-clean-20240814.docx`
- Company template authorities:
  - `/Users/smkzw/Documents/康哲项目资料/模版/方案模版/CMS-D017Ⅰ期方案-v1.1-20260209-clean.docx`
  - `/Users/smkzw/Documents/康哲项目资料/模版/方案模版/CMS-D005-减重II期临床试验方案概要-V0.3-KZYY0525-clean-DIP0526-KZYY0526 (2).docx`
- Current acceptance records:
  - `reviews/codex_prefill_v4_prod_acceptance_20260720.md`
  - `reviews/codex_mw_word_real_acceptance_20260719_review.md`
  - `reviews/codex_mw_docx_indent_synopsis_qc_20260719_review.md`
  - `records/active_slices/medical_writing_cross_indication_reference_gate_20260718/DYNAMIC_CHAPTER_DECISION_MATRIX.md`
- Rejected v1 evidence is a negative fixture only:
  `records/active_slices/medical_writing_ai_first_docx_release_20260720/`.
  Its synthetic providers, generated facts and DOCX outputs must never be reused
  as success evidence.

## Scope

- In scope:
  - write only under
    `records/active_slices/medical_writing_ai_first_docx_release_v2_20260720/`;
  - create one isolated runtime using the same dependency wiring as
    `services/api/app/main.py`, but isolated SQLite/artifact roots and ports;
  - project A must upload the real D017 synopsis through the current product
    synopsis-import path, invoke the configured independent AI task runner,
    expose extracted facts, then apply explicit user confirmation;
  - project B must begin with only `磷酸芦可替尼乳膏`、`特应性皮炎`、`III期`,
    invoke the configured direct `deepseek-v4-pro`, adopt
    `Atopic Dermatitis`, rebuild the versioned search plan, execute the current
    ClinicalTrials.gov discovery service, bind an immutable snapshot, and
    regenerate the evidence-aware package while preserving `user_confirmed`;
  - parse the real RUX protocol from zero with current import/extraction
    surfaces and bind every exact clinical fact to a real locator;
  - generate the full currently applicable dynamic protocol scaffold, not a
    one-section sample, then export two fresh editable DOCX files with the
    current product exporter;
  - inspect OOXML and run the bundled Microsoft365 Open XML validator.
- Out of scope:
  - any stable 5174/8911 database mutation;
  - product source or test edits in this round;
  - old generated DOCX reuse;
  - synthetic AI runner output, recorded provider output, deterministic fake
    provider, hand-written clinical facts, or a one-section greenfield
    shortcut;
  - final Microsoft Word/PDF/visual acceptance, which remains Codex-owned.

## Success Criteria

- Every AI-backed success receipt records the actual configured provider/model,
  prompt version, run ID and source IDs. If production AI is unavailable, the
  corresponding project is failed/partial and no fallback may be counted.
- Project A proves the actual synopsis-import service and explicit confirmation;
  project B proves the actual three-fact AI-first research loop and immutable
  registry snapshot.
- Project B's registry snapshot contains condition/phase/study-type relevant
  public studies and at least one retrievable public Protocol/SAP, or the run
  fails honestly.
- RUX exact dose, endpoint, AESI, sample-size, washout, threshold and visit
  timing facts are source-bound. Missing facts remain blocked.
- Each fresh document uses the full applicable template projection and has real
  Heading 1-4 styles, hierarchical numbering, TOC/SEQ/REF fields,
  bookmarks/hyperlinks, synopsis grouped table, body indentation, Chinese
  `宋体`, Latin/digits `Times New Roman`, black text/tables, headers, footers
  and page numbering.
- Microsoft365 Open XML validation reports zero errors, or a source-preserving
  relative baseline explicitly proves no new error signatures.

## Risk Boundaries

- Write only under
  `records/active_slices/medical_writing_ai_first_docx_release_v2_20260720/`.
- Real project and template files are read-only.
- Do not print credentials. Resolve the product AI provider through current
  application configuration rather than reading or copying secrets.
- Do not perform broad Git or repository cleanup.
- A fake/recorded/synthetic provider branch is forbidden even as a temporary
  success fallback. Preserve the real failure and stop that project.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-20 01:56:18: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-20 01:58: v1 was terminated and rejected after direct source review
  found a synthetic synopsis runner, recorded DeepSeek fallback, no real
  ClinicalTrials.gov discovery/snapshot, and a one-section DOCX shortcut.
