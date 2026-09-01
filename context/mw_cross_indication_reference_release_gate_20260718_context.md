# Task Context: mw_cross_indication_reference_release_gate_20260718

Created: 2026-07-18 12:35:10
Objective: 在隔离运行时以至少三个不同适应症完成公开竞品方案检索、下载、内容校验、章节识别、OCR/Hy-MT翻译/Flash整合QC、语料准入、章节映射、DeepSeek Pro 3-5候选生成和医学质量/前端过程可视化验收，作为医学写作上线硬门
Task type: `complex_delivery_conference`
Risk: `critical`
Selected agent route: `mixed` / `conference:grok-build-grok45-chair+aishuo-cms+opencode-go-deepseek-flash` / `mixed:Grok Build default reasoning; Kimi then Reasonix then qwen then mimo replacement order`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `/Users/smkzw/.codex/AGENTS.md`
- `AGENTS.md`
- `records/USER_REQUIREMENTS_CURRENT_20260718.md`
- `records/active_slices/medical_writing_competitor_corpus_20260712/TASK_RECORD.md`
- `records/active_slices/medical_writing_phase1_autoimmune_mnc_corpus_20260716/TASK_RECORD.md`
- `records/active_slices/medical_writing_prelaunch_acceptance_20260717/TASK_RECORD.md`
- `services/api/app/writing_reference.py`
- `services/api/app/writing_reference_translation_batch.py`
- `services/api/app/ai_gateway.py`
- `frontend/src/features/writing-reference/WritingReferencePanel.jsx`
- ClinicalTrials.gov API v2 and official ClinicalTrials.gov study-document
  download URLs discovered by the product workflow.
- Current local oMLX `http://127.0.0.1:8000/v1/models`, which currently lists
  `GLM-OCR-bf16` and `dawncr0w--Hy-MT2-30B-A3B-oQ8-MLX`.
- Current fixed candidate `http://127.0.0.1:5174/` and API
  `http://127.0.0.1:8911/`; stable real projects remain read-only.

## Scope

- In scope:
  - at least three materially different indications and study designs;
  - fresh product discovery from indication/phase/target intent, study
    selection, official Protocol/SAP download and immutable receipt;
  - file basic-information and content-role/indication/version validation with
    audited user override only for deliberate mismatch testing;
  - text extraction first; GLM-OCR-bf16 only for missing/image pages, with
    figure/table pages rendered at >=200 DPI and up to 8 concurrent OCR jobs;
  - DeepSeek `deepseek-v4-flash` chapter/TOC boundary confirmation, local
    Hy-MT2 chapter-bounded translation, and Flash cross-chunk/cross-section
    integration QC;
  - terminology/numeric/unit/time/negation/abbreviation fidelity checks;
  - source spans, M11/company section applicability, medical review and
    trial-specific corpus admission in an isolated runtime;
  - direct product `deepseek-v4-pro` 3-5 candidates for representative
    background/rationale, population, intervention, endpoint and safety text;
  - senior medical-writer scoring for usability, fluency, scientific accuracy,
    regulatory style, source traceability and unsupported-claim rate;
  - browser evidence for visible discovery/download/parse/translate/QC/review/
    admission/mapping/candidate states, retry and failure recovery.
- Out of scope:
  - automatic medical approval or formal corpus admission in the stable
    production database;
  - editing stable RUX/D001/PNH source projects or source documents;
  - translating entire protocols when a bounded, section-complete sample can
    prove the production path, unless full translation is required to test
    chapter continuity;
  - unrelated monitoring, enrollment or PV changes;
  - commercial Word/document engines or public Sites deployment.

## Success Criteria

- Three indications start from a new product search request; no preselected
  decomposed fragment is allowed to substitute for discovery/download.
- Every selected study has NCT, official URL, document role, version/date,
  byte size, SHA-256 and content-validation revision.
- Every translated sample preserves all source numbers, units, time windows,
  negations and abbreviations, and records OCR/model/prompt/glossary/chunk/
  section lineage.
- Hy-MT2, Flash and Pro are product/external runtime calls, never Codex prose.
- Each indication maps admitted evidence to at least two relevant protocol
  chapters; the production Pro route returns 3-5 distinct candidates and does
  not auto-write the working copy.
- A blinded senior-writer rubric scores each candidate set and records exact
  defects; any scientific fabrication, material mistranslation, wrong
  population/intervention/endpoint, or untraceable claim is P1 and must be
  fixed/re-run.
- Browser screenshots and network/audit evidence show progress, completion,
  retry and failure states without white screen, page-level overflow,
  developer-log clutter or hidden long-running work.
- Stable project/source hashes remain unchanged; isolated databases and
  disposable projects are removed or archived after evidence capture.

## Risk Boundaries

- Stable 5174/8911 is read-only for this slice. All state-changing work uses
  copied databases, random ports and disposable projects.
- Downloaded public documents are immediately usable after technical and
  content validation; no heavy security-scan gate is reintroduced.
- Content mismatch may be overridden only with explicit warning,
  acknowledged codes and an auditable reason.
- Do not expose API keys, protected system prompts, full protocols or clinical
  source text in reports. Bounded quotes and hashes only.
- If the product still routes protocol translation entirely to Flash instead
  of Flash -> Hy-MT2 -> Flash, treat that as an implementation gap and correct
  the architecture before claiming this gate.
- Do not write to production paths until Codex review gate passes and writable
  paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-18 12:35:10: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-18 12:40 CST: Current runtime confirmed direct writing AI
  `deepseek-v4-pro` and legacy reference translation
  `deepseek-v4-flash`; local oMLX exposes GLM-OCR and Hy-MT2. The newer
  Flash -> Hy-MT2 -> Flash protocol translation requirement is not yet proven
  in the product and is part of this release gate.
