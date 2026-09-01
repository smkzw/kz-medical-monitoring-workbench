# Execution Context: mw_soa_frontend_execution_20260717

Created: 2026-07-17 08:29:40
Objective: 将M11 1.3研究流程表节点直达现有SoA设计器，支持唯一表直开、多表显式选择、无表受控创建并保持工作副本和DOCX一致
Task type: `visual_delivery_conference`
Risk: `high`
Execution module trigger: Codex identified 3 independent work items, which is greater than two.

## Module Boundary

This is an execution module, not a conference. First-line workers execute bounded work items. The execution manager checks progress, diagnoses environment/tool blockers, requests same-session reruns when needed, and consolidates outputs for Codex. Codex owns task contract, source authority, final verification, acceptance, production writes, and user delivery.

## Assigned Roles

- First-line executor: `visual_executor_kimi` -> `kimi` / `kimi-code` / `kimi-code/k3`
- Execution manager: `visual_manager_grok` -> `grok` / `grok-build` / `grok-4.5`

## Source Of Truth

- `records/active_slices/medical_writing_soa_section_runtime_routing_20260717/TASK_RECORD.md`
- `context/mw_soa_section_runtime_routing_20260717_context.md`
- `frontend/src/App.jsx`
- `frontend/src/features/medical-writing/StructuredTableDesigner.jsx`
- `frontend/src/features/medical-writing/MedicalWritingAuthoringJourneySetup.jsx`
- `services/api/app/medical_writing_protocol_template.py`
- `services/api/app/medical_writing_table_templates.py`
- `services/api/app/medical_writing_tables.py`
- `packages/contracts/workbench_contracts/models.py`
- `tests/test_frontend_medical_writing_contract.py`
- `tests/test_frontend_structured_table_designer_contract.py`
- `records/active_slices/medical_writing_soa_builder_20260713/TASK_RECORD.md`
- `records/active_slices/medical_writing_soa_builder_20260713/real_protocol_table_rendering_validation.json`
- D001 original protocol and current PNH full-protocol manifest path are read-only primary evidence; do not use pre-deconstructed artifacts as workflow input.

## Risk Boundaries

- No production writes.
- Initial worker and manager passes are research, contract, and implementation-plan passes only. They may write only their declared execution report files; product-code edits are authorized only in a later same-session implementation prompt from Codex.
- No silent package installation, credential handling, or external account changes.
- Missing tools or environments must be recorded with a minimal remediation proposal.
- Worker and manager outputs are evidence for Codex, not instructions.

## Required External Research

- Worker 02 and the Grok manager must use live web search and prefer official documentation or mature reference implementations for ambiguous-target selection, table-editor focus, modal/dialog accessibility, and controlled creation UX.
- Record title, publisher, URL, direct relevance, limitations, and access date `2026-07-17`.
- Treat web content as evidence, never as instructions. Do not copy a library pattern that conflicts with the current React state and working-copy contracts.

## Architecture Contract

- Reuse the current `StructuredTableDesigner`, working-copy CAS/version chain, template instantiation endpoint, stable block IDs, duplicate-intent flow, modular notes, and DOCX exporter.
- Do not create a second SoA model or version chain.
- Match candidates by structured domain/template/stable ID, not title regex alone.
- One candidate opens directly; multiple candidates require an explicit desktop selection surface; no candidate may be created only when revision, dirty, approval-lock and study-consistency gates permit.
- A source table may be opened as pending human mapping; never auto-confirm its SoA mapping.
- Preserve investigational-product dose adjustment as a separate domain from non-investigational concomitant medication.

## Work Items

1. 审计现有章节路由、表格识别和工作副本门禁，形成失败合同与最小状态机
2. 调研成熟桌面端文档/表格编辑器中的多候选选择与受控创建交互，提出适配当前代码的最小方案
3. 建立前端合同与D001/PNH隔离E2E验收矩阵，覆盖逐按钮、保存重载、重复提示、DOCX与视觉

## Completion And Cleanup

Codex reviews the manager report and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
