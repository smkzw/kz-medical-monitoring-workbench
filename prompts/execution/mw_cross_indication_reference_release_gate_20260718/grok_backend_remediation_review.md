# Role

You are the execution manager for a production-critical medical-writing backend
remediation. First fully read and comply with `/Users/smkzw/.hermes/SOUL.md`
and `/Users/smkzw/.codex/AGENTS.md`. This is an execution review, not a
consensus conference. Codex is the final architecture, clinical, regulatory,
production-write, and release authority.

# Objective

Review the current W1 backend implementation against the real production
composition and produce a precise remediation plan for the existing CMS worker
session. Do not edit product files in this pass. The output must make the
smallest production-correct path explicit.

# Source Of Truth

Read these files only:

- `context/mw_cross_indication_reference_release_gate_20260718_context.md`
- `runs/execution/mw_cross_indication_reference_release_gate_20260718/manager_plan.md`
- `records/active_slices/medical_writing_cross_indication_reference_gate_20260718/TASK_RECORD.md`
- `records/active_slices/medical_writing_cross_indication_reference_gate_20260718/ACCEPTANCE_CONTRACT.md`
- `records/USER_REQUIREMENTS_CURRENT_20260718.md`
- `services/api/app/main.py`
- `services/api/app/writing_reference.py`
- `services/api/app/writing_reference_translation_batch.py`
- `services/api/app/chapter_translation_pipeline.py`
- `services/api/app/ocr_gateway.py`
- `services/api/app/ai_gateway.py`
- `services/api/app/ai_task_runner.py`
- `packages/contracts/workbench_contracts/models.py`
- `tests/test_chapter_translation_pipeline.py`
- `tests/test_writing_reference_translation_batch.py`
- `runs/execution/mw_cross_indication_reference_release_gate_20260718/cms_w1_backend_implementation.md`

Hard boundaries:

- Product source files, tests, runtime databases, model settings and stable
  services are read-only in this review pass.
- Web research is permitted only when an implementation uncertainty genuinely
  requires authoritative current documentation; record every target and
  observation.
- Do not read secrets, credentials, unrelated projects or unrelated source
  files.
- Do not run live model generation or write to stable ports/databases.
- Write exactly one output file:
  `runs/execution/mw_cross_indication_reference_release_gate_20260718/grok_backend_remediation_review.md`.

# Confirmed Codex Rejection Findings

Treat these as observed evidence to verify in source:

1. `main.py` does not inject `ChapterTranslationPipeline`, so production keeps
   `chapter_pipeline=None`.
2. If injected, `_process_claimed_item()` first runs the new pipeline only for
   lineage, then calls the old `WritingReferenceTranslationService.translate()`
   again. The persisted final translation can therefore still be produced by
   the old Flash-only body translator and causes duplicate AI work.
3. `_update_pipeline_stages()` passes `ocr_page_lineage=()` unconditionally;
   real PDF page triage, >=200 DPI rendering, GLM-OCR and recovered text are not
   part of the candidate.
4. Pipeline stage updates are persisted only after the whole injected pipeline
   returns, so long-running intermediate stages are not genuinely observable.
5. Focused tests pass but do not prove production composition or that the old
   body translator is never called.

# Required Production Semantics

- final candidate body text must come from local
  `dawncr0w--Hy-MT2-30B-A3B-oQ8-MLX`;
- `deepseek-v4-flash` only plans TOC/chapter boundaries and performs
  integration/seam QC;
- text extraction comes first; missing/image/spatial pages route to local
  `GLM-OCR-bf16`, max 8 concurrent, >=200 DPI for figure/table/spatial pages;
- source and OCR text must feed the chapter plan and body translation;
- deterministic fidelity checks remain blocking before candidate readiness;
- medical approval remains required before corpus admission;
- retries/idempotency/restart recovery and lineage must remain intact;
- no fallback may silently replace an unavailable required model;
- stable ports 5174/8911, stable DBs, real projects and source files are
  read-only;
- the product must run independently of Codex/Hermes;
- do not introduce paid/commercial services.

# Questions To Resolve

1. Which existing production abstractions should be reused for local oMLX
   OpenAI-compatible translation and OCR, and which minimal new adapters are
   required?
2. Should the new pipeline replace
   `WritingReferenceTranslationService.translate()` internally or should the
   batch service call a new authoritative service? Choose one and justify it
   based on compatibility and blast radius.
3. How should extracted page/block data reach OCR triage without re-parsing the
   full PDF for every span?
4. How should real intermediate stage transitions be persisted atomically and
   exposed through the existing batch API?
5. Which focused unit/integration/live-smoke tests are mandatory to prove the
   production path, including a spy assertion that the legacy Flash-only body
   path is not invoked?
6. Identify any unsafe or overbuilt parts in the W1 implementation that should
   be removed instead of extended.

# Output Contract

Return:

1. source files read;
2. verified observations with file/line references;
3. exact proposed call graph;
4. bounded file-by-file remediation assignments;
5. required tests and expected assertions;
6. migration/backward-compatibility risks;
7. failed paths and uncertainty;
8. a compact LOOP trace and recommended next step for the CMS same-session
   remediation.

Do not claim release acceptance. Do not edit product files. Write the complete
report to
`runs/execution/mw_cross_indication_reference_release_gate_20260718/grok_backend_remediation_review.md`.
