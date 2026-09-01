# Task Context: mw_slice_a_competitor_docs_20260726

Created: 2026-07-26 17:51:45
Objective: 在现有医学写作系统中完成真实竞品篮子确认与公开Protocol/SAP原文下载切片：只补齐阻断真实页面选择、来源版本记录、下载失败显式化和原始文件入库的有限缺口，并返回变更文件、测试和浏览器复核定位；禁止重复审计已验收分诊逻辑，禁止确认PNH篮子或使用假文件
Task type: `finite_code_task`
Risk: `critical`
Selected agent route: `aishuo` / `cms-model` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `records/handoffs/codex_retake_20260726/NEXT_LAUNCH_EXECUTION_PLAN_20260726.md`
- `records/handoffs/codex_retake_20260726/00_AUDIT_JOURNAL.md`
- `services/api/app/writing_reference_preparation_batch.py`
- `services/api/app/writing_reference.py`, read-only for the real document
  client and ingest error contract.
- `services/api/app/writing_reference_repository.py`
- `services/api/app/main.py`, limited to writing-reference preparation and
  triage-confirmation routes.
- `packages/contracts/workbench_contracts/models.py`, limited to the relevant
  preparation/download/source-provenance contracts.
- `tests/test_writing_reference_preparation_batch.py`
- `tests/test_writing_reference_repository.py`
- `tests/test_writing_reference_api.py`
- `records/handoffs/codex_retake_20260726/evidence/independent_ai/pnh_v20_four_abbrev_scientific_check.json`
- The running local API on `127.0.0.1:8911` after Codex reports the active
  v20 job terminal.

## Scope

- In scope:
  - inspect the existing product path from a confirmed immutable competitor
    basket to public Protocol/SAP preparation;
  - run a real download in an isolated test project using a source URL already
    present in a search snapshot;
  - patch only a demonstrated blocker in idempotent download, source/version
    provenance, explicit failure reporting, or raw artifact persistence;
  - add focused tests for every changed behavior.
- Out of scope:
  - competitor indication/phase/modality triage logic;
  - confirming or projecting the PNH v20 basket;
  - document-content override, OCR, translation, corpus admission, authoring,
    visual redesign or DOCX export;
  - broad repository, security or performance audit.

## Success Criteria

- No code change is required when the real path already passes.
- A retained public Protocol/SAP can be downloaded from its real registered
  source URL into the project-owned artifact store without Codex or worker
  model content substitution.
- Persisted evidence includes NCT ID, document ID/type, requested URL, final
  URL, filename, source time/version fields available from the registry,
  content hash, byte size and artifact locator.
- Retry is idempotent and does not overwrite unrelated or manually uploaded
  files.
- Network/type/content failures are explicit per item; no placeholder PDF or
  synthetic success may be created.
- Focused tests and one isolated real API exercise pass. Return only changed
  files, checks, remaining blockers and evidence locators.

## Risk Boundaries

- Writable production paths are limited to:
  - `services/api/app/writing_reference_preparation_batch.py`
  - `services/api/app/writing_reference_repository.py`
  - the directly required preparation contracts in
    `packages/contracts/workbench_contracts/models.py`
  - focused `tests/test_writing_reference_*.py`
- `services/api/app/main.py` is read-only unless a demonstrated route wiring
  blocker cannot be fixed within the writable list; if so, stop and report the
  exact locator instead of editing it.
- Do not restart the shared runtime, confirm any real basket, write to the PNH
  project, or delete artifacts.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-26 17:51:45: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-26: Codex narrowed the task to backend preparation/download and
  source-provenance behavior. Frontend/browser acceptance will be a separate
  visual/browser execution slice.
- 2026-07-26: First execution pass is not accepted. It proved a direct
  `WritingReferenceDocumentService.ingest` real download in a temporary
  directory, but `step4_prep_batch.json` records `rc=22` and `batch=null`;
  therefore no real running-API preparation batch reached the project-owned
  artifact store. Its failure probe also records `is_explicit=false` because
  the generic `ingest_failed` code has no product-specific failure category.
