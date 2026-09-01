# Task Context: medical_writing_cross_table_coexistence_20260714

Created: 2026-07-14 03:15:21
Objective: 验证研究流程表、五类领域表与原始方案表格在同一真实工作副本中的保存、审批、重启和Word导出互不串扰
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `reasonix-cli` / `deepseek-v4-pro` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `records/active_slices/medical_writing_domain_table_designers_20260714/TASK_RECORD.md`
- `services/api/app/medical_writing_table_templates.py`
- `services/api/app/medical_writing_tables.py`
- `services/api/app/medical_writing_repository.py`
- `services/api/app/medical_writing_document_exporter.py`
- `tests/test_medical_writing_real_project_flow.py`
- `tests/test_medical_writing_document_export_api.py`
- `tests/test_medical_writing_table_templates.py`
- Real project fixtures already bound by `MedicalWritingDocumentService`: RUX-03-002, CMS-D001, MY008211A-PNH-3-01 original protocol DOCX.

## Scope

- In scope: One saved working copy containing original source tables, one generated Schedule of Activities table, and all five promoted/guarded domain tables; cold restart; per-table state preservation; approval blockers; draft Word order and visible table rendering.
- In scope: At least two real projects; prefer all three currently registered real protocols.
- Out of scope: Browser visual acceptance in this slice; tracked changes; electronic signature; project-specific medical threshold validation; source DOCX modification.

## Success Criteria

- Original source tables remain present and unchanged after generated tables are added.
- Schedule of Activities data does not acquire non-SoA domain profile state; promoted profiles do not acquire SoA mapping state.
- Editing or confirming one profile does not change any sibling table's ids, semantic roles, profile state, notes or source locators.
- Approval blockers identify only the table and missing condition that caused each blocker; C-grade generic and raw source tables do not become newly blocked.
- Save, cold restart, reload and draft Word export preserve table order, titles, visible cells, notes and semantic roles for all generated tables.
- Focused tests and full repository regression pass; any shared-contract conflict is fixed at the source rather than special-cased per project.

## Risk Boundaries

- Test-first. Production writes are allowed only if a failing coexistence contract proves a shared implementation defect.
- Do not alter or overwrite original DOCX fixtures.
- Do not relax approval, source, audit, AI or Word validation to make coexistence tests pass.
- Do not add project ids, drug names, thresholds or indication-specific rules to shared code.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-14 03:15:21: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-14 03:18: Context completed from the accepted domain-profile slice; no browser use authorized.
- 2026-07-14 03:20: First prompt preflight failed because the exporter filename was wrong and the generated prompt used an absolute workspace path. Corrected both before dispatch; no agent run occurred.
