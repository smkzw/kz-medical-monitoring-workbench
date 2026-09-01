# Execution Context: mw_design_projection_unification_20260724

Created: 2026-07-24 17:23:35
Objective: 将动态研究设计收敛为单一权威投影并完成实际输出级回归
Task type: `complex_delivery_conference`
Risk: `high`
Execution module trigger: Codex identified 3 independent work items, which is greater than two.

## Module Boundary

This is an execution module, not a conference. Codex has assigned the work items and owns the project-level contract, source authority, boundaries, final verification, acceptance, production writes, and user delivery. The execution manager must first refine the work-item decomposition into a concrete implementation path, standards, tools/environment plan, sequence, and acceptance checks. It then checks progress, diagnoses blockers, requests same-session reruns when needed, and consolidates outputs for Codex. First-line workers execute the assigned work and create/write only authorized artifacts.

## Assigned Roles

- First-line executor: `complex_executor_cms` -> `hermes` / `aishuo` / `cms-model`
- Execution manager: `complex_manager_grok` -> `grok` / `grok-build` / `grok-4.5`
- Execution-manager fallback: `use the declared role fallbacks`

## Source Of Truth

- Product requirements and current release gap:
  - `records/active_slices/medical_writing_production_rebaseline_20260722/TASK_RECORD.md`
  - `records/active_slices/medical_writing_production_rebaseline_20260722/CURRENT_GAP_MATRIX.md`
  - `reviews/medical_writing_dynamic_design_projection_review_20260724.md`
- Authoritative contracts and implementation:
  - `packages/contracts/workbench_contracts/models.py`
  - `services/api/app/medical_writing_protocol_assembly_plan.py`
  - `services/api/app/medical_writing_protocol_template.py`
  - `services/api/app/medical_writing_plan_consumption.py`
  - `services/api/app/medical_writing_authoring_journey.py`
  - `services/api/app/medical_writing_table_templates.py`
  - `services/api/app/medical_writing_study_schema.py`
  - `services/api/app/medical_writing_document_exporter.py`
- Current decisive tests:
  - `tests/test_medical_writing_structured_design_contract.py`
  - `tests/test_worker01_typed_phase1_parts_and_safe_prefill.py`
  - `tests/test_worker02_plan_consumption_cross_projection.py`
  - `tests/test_medical_writing_protocol_template.py`
  - `tests/test_medical_writing_dynamic_section_matrix.py`
  - `tests/test_medical_writing_study_schema.py`
  - `tests/test_medical_writing_table_templates.py`
  - `tests/test_medical_writing_document_exporter.py`
- Highest-priority Chinese protocol and synopsis references remain the locally
  designated CMS templates and CMS-D017 PNH synopsis. ICH M11 is a framework
  reference, not authority to overwrite the company format.

## Risk Boundaries

- Functional and scientific work only. Do not search for, inspect, or report
  security vulnerabilities, backdoors, penetration findings, or hardening work.
- First manager pass is planning/review only and may write only its
  runner-managed report. No production source edits in that pass.
- Later workers may edit only the explicitly assigned non-overlapping files
  after Codex accepts the manager plan. Preserve all unrelated user and agent
  changes. Do not reset or revert the worktree.
- No package installation, credential handling, external account changes, or
  substitution of an execution model for the product's independent AI.
- Clinical meaning must fail closed when a selected typed design lacks the
  information needed for deterministic projection. Do not fill missing dose,
  switch, crossover, OLE, adaptive, or statistical details by assumption.
- Existing boolean and free-text fields require a deterministic backward
  migration path. New structured facts must become the authority; free text is
  fallback only while the structured state is undecided.
- Worker and manager outputs are evidence for Codex. Codex owns final source,
  medical/scientific, runtime, browser, DOCX and release acceptance.

## Success Criteria

1. One normalized projection derived from `StudyDefinition` supplies all
   design facts consumed by synopsis, body applicability/content, SoA, study
   schema/flowchart and DOCX assembly.
2. Selected but unresolved Phase I Parts and complex designs block only the
   affected deterministic outputs and present precise missing facts.
3. Treatment switching, crossover, OLE, blinded/unblinded sample-size
   re-estimation and adaptive design have semantically distinct typed objects,
   migration behavior and consistency checks.
4. Phase III outputs cannot leak stale Phase I Parts; crossover is never
   rendered as ordinary treatment switching.
5. Output-level tests assert actual synopsis text/rows, body sections, SoA
   cells/footnotes, flowchart nodes/edges and DOCX content for the specified
   I/III and complex-design matrix.
6. Focused and adjacent test suites pass. Any remaining product gaps are
   explicit and are not relabeled as complete.

## Timeout And Stop Policy

- External hard wait: 120 minutes. Do not send status prompts while a pass is
  running.
- Stop and report rather than guessing if source authority conflicts, a
  migration would destroy user data, or a file ownership overlap remains.
- Repeated identical failure without new evidence triggers a different
  decomposition or a targeted Codex decision.

## Allowed Output Paths

- First manager pass:
  `runs/execution/mw_design_projection_unification_20260724/manager.md`
  through the runner only.
- Worker reports:
  `runs/execution/mw_design_projection_unification_20260724/worker_0*.md`
  through their runners only.
- Production source/test write paths will be assigned after manager
  decomposition; no worker may infer additional ownership.

## Work Items

1. 设计NormalizedDesignProjection合同、StudyDefinition归一化入口、legacy自由文本回退边界和I期unresolved blocker
2. 设计并实现转组、交叉、OLE、样本量再估计、适应性设计typed对象及迁移/一致性校验
3. 将摘要、正文适用性、SoA、流程图、DOCX消费统一投影并建立多设计实际成品测试矩阵

## Completion And Cleanup

Codex reviews the manager report and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
