# Task Context: writing_reference_real_batch_20260725

Created: 2026-07-25 01:01:19
Objective: 只读盘点两个不同真实项目的最小写作参考生产批次，并形成可直接执行、可恢复、证据持久化的批次合同；不修改代码、不运行服务或模型、不联网下载
Task type: `clinical_document_router`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Global instructions: `/Users/smkzw/.codex/AGENTS.md`.
- Workspace instructions: `AGENTS.md`.
- Release priority: `reviews/medical_writing_next_release_priorities_20260725.md`, item 1.
- Product implementation:
  - `services/api/app/writing_reference_preparation_batch.py`
  - `services/api/app/writing_reference_translation_batch.py`
  - `services/api/app/chapter_translation_pipeline.py`
  - `services/api/app/writing_reference.py`
  - `services/api/app/main.py`
- Admission QC entry: `scripts/qc/writing_reference_admission_e2e.py`.
- Original source candidates:
  - `/Users/smkzw/Documents/康哲项目资料/竞品调研/CRSwNP/03_Protocols/【IL-4Rα】【Dupilumab】【Sanofi_Regeneron】【Phase3】【FDA已获批】【2019】【关键III期】【SINUS-24】【NCT02898454】【FDA已获批_NMPA未获批_EMA已获批_PMDA已获批】【Protocol】.pdf`
  - `/Users/smkzw/Documents/朗来项目资料/竞品分析/UC/JAKi Upadacitinib AbbVie/【NCT02819635 IIb-III期 诱导+维持】方案.pdf`
- Current runtime state was inspected read-only. With no
  `WORKBENCH_RUNTIME_DIR` override, `services/api/app/main.py` resolves the
  canonical runtime to `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/runtime`.

## Scope

- In scope: source-file inventory, byte/page/text/OCR characterization,
  current API/job/model call-point mapping, configuration and recovery gap
  analysis, and a directly executable future batch contract.
- Out of scope: code or test changes, runtime/SQLite writes, service or model
  startup, model inference, ClinicalTrials.gov download, medical approval,
  corpus admission, and production release.

## Success Criteria

- Select one native-text and one OCR-required original Protocol/SAP from two
  different real workbench projects.
- Record absolute path, role, SHA-256, page/OCR profile, expected chapter
  contract, content checks, model call points, API/job entry points,
  configuration gaps, recovery behavior, and persistent evidence layout.
- Write the reviewed result to
  `reviews/writing_reference_real_batch_candidates_20260725.md`.
- End with the safest next command/interface sequence; do not execute it in
  this read-only turn.

## Risk Boundaries

- Do not modify product code, tests, source PDFs, or runtime databases.
- Do not use `(OCR)` copies, pre-deconstructed corpora, skill outputs, or
  extracted intermediates as source authority.
- Do not call or start GLM-OCR, Hy-MT2, DeepSeek, or any network downloader.
- Sponsor confidentiality/rights language and snapshot `rights_status` must
  be resolved before future model execution.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-25 01:01:19: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-25: Read all named implementation/QC files, the directly relevant
  task records, and the complete related test files through full-file parsing.
- 2026-07-25: Read-only PDF inventory selected NCT02898454 (native text) and
  NCT02819635 (mixed native text plus 12 full-page image pages). No model,
  service, database write, or internet call was performed.
- 2026-07-25: Identified two release blockers outside the model runtimes:
  no implemented per-stage Flash-to-Pro escalation and no persistence of the
  200 DPI OCR input PNGs required by the release evidence contract.
