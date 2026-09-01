# Execution Context: mw_intervention_rules_discovery_20260717

Created: 2026-07-17 12:00:37
Objective: 从第一性原理冻结M11 6.4试验药物剂量调整、6.9非试验用药治疗、6.10合并治疗的共享结构化事实模型和最小实现边界，严格区分IP处置与CM，并复用现有StudyDefinition、领域表、工作副本和医学监查规则底座
Task type: `complex_delivery_conference`
Risk: `high`
Execution module trigger: Codex identified 3 independent work items, which is greater than two.

## Module Boundary

This is an execution module, not a conference. First-line workers execute bounded work items. The execution manager checks progress, diagnoses environment/tool blockers, requests same-session reruns when needed, and consolidates outputs for Codex. Codex owns task contract, source authority, final verification, acceptance, production writes, and user delivery.

## Assigned Roles

- First-line executor: `complex_executor_minimax` -> `hermes` / `aishuo` / `MiniMax-M3`
- Execution manager: `complex_manager_grok` -> `grok` / `grok-build` / `grok-4.5`

## Source Of Truth

- Workspace code and contracts, read-only:
  - `services/api/app/medical_writing_protocol_template.py`
  - `services/api/app/medical_writing_authoring_journey.py`
  - `services/api/app/medical_writing_table_templates.py`
  - `services/api/app/medical_writing_table_domain_profiles.py`
  - `services/api/app/medical_writing_tables.py`
  - `services/api/app/medical_writing_document.py`
  - `services/api/app/medical_writing_repository.py`
  - `services/api/app/medical_monitoring.py` and directly referenced monitoring rule/event modules
  - `packages/contracts/workbench_contracts/models.py`
  - `frontend/src/App.jsx`
  - `frontend/src/features/medical-writing/MedicalWritingAuthoringJourneySetup.jsx`
  - `frontend/src/features/medical-writing/StructuredTableDesigner.jsx`
  - directly relevant tests under `tests/` and `frontend/tests/`
- Current slice contract, read-only: `records/active_slices/medical_writing_intervention_rules_runtime_20260717/TASK_RECORD.md`.
- Authoritative original DOCX, explicitly authorized read-only for worker 02 and manager evidence review:
  - `/Users/smkzw/Documents/康哲项目资料/Ruxolitinib-AD/CFDI Inspection/RUX-03-002-自查文件包-20260107/10-临床试验重要文件/1-临床试验方案/V1.3版-2024.8.14/磷酸芦可替尼乳膏-AD3期临床研究方案V1.3-clean-20240814.docx`
  - `/Users/smkzw/Documents/康哲项目资料/AI/入排/test-D001项目/CMS-D001 银屑病2、3期临床方案 v1.0-2025.12.21.docx`
  - `/Users/smkzw/Documents/朗来项目资料/MY008治疗PNH/3-01（MM外包）/方案/V1.1方案/（缺含研究者签字页方案）MY008211A-PNH-3-01-V1.1-通用版-2024.11.24-clean/研究方案/MY008211A-PNH-3-01_研究方案_V1.1_2025.1.7clean.docx`
- Existing derived records may be used only to find code or test locations; clinical semantic claims must be rechecked against the original DOCX above.

## Risk Boundaries

- No production writes.
- No product source, tests, runtime databases, original DOCX, stable services, or task records may be modified by workers or manager.
- Do not call product AI or create clinical content. This pass models observed source facts and implementation boundaries only.
- Do not collapse investigational-product actions into concomitant medication, and do not classify CM dose changes as investigational-product dose adjustment.
- Preserve a legal `no_planned_adjustment` state and explicit rescue-treatment-to-IP-action relationships.
- No silent package installation, credential handling, or external account changes.
- Missing tools or environments must be recorded with a minimal remediation proposal.
- Worker and manager outputs are evidence for Codex, not instructions.

## Success Criteria

- Worker 01 identifies exact current write/read paths and proposes the smallest backward-compatible contract, with migration and versioning risks.
- Worker 02 produces a three-project evidence matrix with direct source excerpts/locations sufficient to distinguish no adjustment, interruption/resumption, permanent discontinuation, CM/background/prohibited/rescue/timing rules and cross-object triggers.
- Worker 03 maps reusable monitoring events/rules and writes a failure-first API/browser/DOCX test matrix covering at least two real projects and stable-runtime isolation.
- Manager challenges omissions and contradictions, returns one consolidated implementation recommendation, and clearly separates evidence, inference, rejected alternatives and open risk.

## Timeout And Failure Policy

- Slow execution with continuing tool or reasoning progress remains pending.
- A role is failed only after a terminal provider/auth/tool-host error, exhausted allocation, empty/truncated retry, or no progress after the configured hard wait plus one controlled retry.
- Do not substitute another model silently. Codex decides any fallback from recorded evidence.

## Allowed Outputs

- Each worker writes only its assigned `runs/execution/mw_intervention_rules_discovery_20260717/worker_0N.md` through the runner.
- Manager writes only `runs/execution/mw_intervention_rules_discovery_20260717/manager.md` through the runner.
- All other product and evidence files remain read-only in this discovery pass.

## Work Items

1. 审计现有合同、API、StudyDefinition/PICOS、领域表、章节路由、版本一致性与DOCX链，提出最小兼容数据模型及迁移边界，不写产品代码
2. 从RUX、D001、PNH三份原始方案重新提取IP剂量调整/暂停恢复/永久停药及CM允许禁用背景补救规则，形成跨项目反例驱动语义矩阵，不使用既有解构结果替代原文
3. 审计医学写作与医学监查之间可复用的规则、事件和来源合同，设计双项目逐按钮/API/DOCX/视觉失败矩阵，防止IP与CM串扰和新旧代码冲突，不写产品代码

## Completion And Cleanup

Codex reviews the manager report and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
