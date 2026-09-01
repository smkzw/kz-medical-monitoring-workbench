# Task Context: mw_source_reference_reindex_20260722

Created: 2026-07-22 10:08:33
Objective: 根因修复导入方案原有引文扫描与受控重索引误判，限定扫描器和测试文件，真实RUX/D001回归、OOXML安全与幂等验收
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/medical_writing_source_reference_reindex.py`
- `tests/test_medical_writing_source_reference_reindex.py`
- `tests/test_medical_writing_source_preserving_export.py`
- Immutable RUX source resolved by `MedicalWritingDocumentService.original_protocol_path('proj_rux_03_002')`.
- Immutable D001 source resolved by `MedicalWritingDocumentService.original_protocol_path('proj_d001')`.
- Microsoft Learn WordprocessingML style, paragraph-outline and table structure documentation.

## Scope

- In scope: reference-section boundary, table-formatted references, citation-manager field classification, first-occurrence ordering, orphan notices, fail-closed transform guards, synthetic and real-project regressions.
- Out of scope: exporter, literature, main, models, repository, frontend and all source DOCX writes.

## Success Criteria

- RUX appendix tables are excluded and true references/citations are counted from the manifest.
- D001 is scanned as a second real project without source mutation.
- EndNote/Zotero/Mendeley fields remain intact; unsafe renumbering blocks with an actionable reason.
- Split runs, superscript, hyperlink, REF field, missing target, duplicate identity, orphan and range cases are covered.
- Safe transforms are idempotent and preserve package part names/non-target parts.
- `PytestUnhandledThreadExceptionWarning` is treated as an error.

## Risk Boundaries

- Modify only the scanner and allowed tests; do not modify exporter/literature/main/models/repository/frontend.
- Never write RUX or D001 source files.
- Do not remove or rewrite citation-manager ADDIN metadata.
- Do not convert a scanning uncertainty into a permissive apply decision.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-22 10:08:33: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-22: Reproduced RUX 40 groups/15 citations and D001 51 groups/14 citations with the pre-fix scanner.
- 2026-07-22: Root cause isolated to unresolved paragraph-style inheritance, overlong reference-region scanning and blanket manager-field blocking.
- 2026-07-22: Implemented bounded scan/decision changes and synthetic/real-project tests.
- 2026-07-22: Final adjacent regression 99 passed; no PytestUnhandledThreadExceptionWarning.
