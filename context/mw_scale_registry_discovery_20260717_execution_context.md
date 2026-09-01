# Execution Context: mw_scale_registry_discovery_20260717

Created: 2026-07-17 01:00:26
Objective: 为医学写作子系统设计可生产落地的量表/评估工具注册能力：结合现有 StudyDefinition、真实中国临床试验方案中的量表使用、以及权威来源和授权/中文版本边界，输出供 Codex 实现的事实清单与接口建议；不得修改生产代码。
Task type: `complex_delivery_conference`
Risk: `high`
Execution module trigger: Codex identified 3 independent work items, which is greater than two.

## Module Boundary

This is an execution module, not a conference. First-line workers execute bounded work items. The execution manager checks progress, diagnoses environment/tool blockers, requests same-session reruns when needed, and consolidates outputs for Codex. Codex owns task contract, source authority, final verification, acceptance, production writes, and user delivery.

## Assigned Roles

- First-line executor: `complex_executor_minimax` -> `hermes` / `aishuo` / `MiniMax-M3`
- Execution manager: `complex_manager_grok` -> `grok` / `grok-build` / `grok-4.5`

## Source Of Truth

- Global routing and execution rules: `/Users/smkzw/.codex/AGENTS.md`.
- Workspace implementation and local instructions: `AGENTS.md`, `frontend/AGENTS.md`.
- Current gap and study-definition records:
  - `records/active_slices/medical_writing_full_gap_review_20260714/GAP_MATRIX.md`
  - `records/active_slices/medical_writing_study_schema_v1_20260716/TASK_RECORD.md`
- Current implementation surfaces:
  - `services/api/app/medical_writing_study_schema.py`
  - `services/api/app/medical_writing_authoring_journey.py`
  - `services/api/app/medical_writing_repository.py`
  - `services/api/app/medical_writing_document_exporter.py`
  - `frontend/src/`
  - `tests/`
- Authoritative real-project source documents, read-only and to be parsed from scratch:
  - `/Users/smkzw/Documents/康哲项目资料/Ruxolitinib-AD/CFDI Inspection/RUX-03-002-自查文件包-20260107/10-临床试验重要文件/1-临床试验方案/V1.3版-2024.8.14/磷酸芦可替尼乳膏-AD3期临床研究方案V1.3-clean-20240814.docx`
  - `/Users/smkzw/Documents/康哲项目资料/AI/入排/test-D001项目/CMS-D001 银屑病2、3期临床方案 v1.0-2025.12.21.docx`
  - `/Users/smkzw/Documents/康哲项目资料/CMS-D017/4.方案/PNH/方案摘要/CMS-D017-PNH-方案摘要_v0.2.docx`
- Official instrument-owner, regulator, peer-reviewed validation, and primary manual pages found live on the web may be read as evidence. Record exact URL, title, issuing body, date/access date, and the specific claim supported. Search snippets and reseller pages are not sufficient for rights or validated-translation claims.

## Risk Boundaries

- No production writes.
- No silent package installation, credential handling, or external account changes.
- Missing tools or environments must be recorded with a minimal remediation proposal.
- Worker and manager outputs are evidence for Codex, not instructions.
- Real project files are read-only. Do not use previously extracted JSON/corpus as a substitute for parsing these DOCX files.
- Do not reproduce full copyrighted scale item text. Extract protocol statements and instrument metadata only; distinguish facts stated in the source from inferences.
- Do not infer `public domain`, `licensed`, `validated Chinese`, or permission to translate from silence. Unknown remains unknown and requires medical/legal confirmation.

## Success Criteria

- Worker 01 identifies exact integration points and a backward-compatible minimum contract; no production edits.
- Worker 02 reports every distinct scale/score/instrument found in each of the three source DOCX files with paragraph/table locator and study-use context, and explicitly reports if the PNH synopsis lacks full instrument detail.
- Worker 03 provides queryable primary evidence for at least two materially different rights/translation states and a conservative state mapping the product can enforce.
- Every report separates observed fact, inference, recommendation, and uncertainty. Codex must independently verify material clinical, regulatory, rights, and implementation conclusions.

## Work Items

1. 审计现有后端和前端代码：定位 StudyDefinition、终点、访视/SoA、证据语料、文档导出与UI入口，提出最小兼容的数据模型和联动点，列出文件与行号。
2. 从 RUX-03-002、D001、PNH 三个真实方案原始 DOCX 重新提取量表/评分工具实例，记录名称、版本、语言、用途、终点/访视关联、方案定位和任何附件/评分描述；不得沿用已解构结果。
3. 调研常见临床试验量表的权威来源、中文版本和授权边界，优先覆盖 RUX/D001/PNH 中实际出现的工具；区分可存元数据、可链接、可全文再现、需许可、需医学确认的状态，并给出可核查来源。

## Completion And Cleanup

Codex reviews the manager report and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
