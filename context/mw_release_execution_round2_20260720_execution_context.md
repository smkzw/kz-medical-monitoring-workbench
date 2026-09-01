# Execution Context: mw_release_execution_round2_20260720

Created: 2026-07-20 12:39:49
Objective: 完成医学写作子系统结构化设计事实、12-lane双入口真实E2E、独立AI和Word发布验收，执行模型实施，Codex最终验收
Task type: `complex_delivery_conference`
Risk: `critical`
Execution module trigger: Codex identified 3 independent work items, which is greater than two.

## Module Boundary

This is an execution module, not a conference. Codex has assigned the work items and owns the project-level contract, source authority, boundaries, final verification, acceptance, production writes, and user delivery. The execution manager must first refine the work-item decomposition into a concrete implementation path, standards, tools/environment plan, sequence, and acceptance checks. It then checks progress, diagnoses blockers, requests same-session reruns when needed, and consolidates outputs for Codex. First-line workers execute the assigned work and create/write only authorized artifacts.

## Assigned Roles

- First-line executor: `complex_executor_cms` -> `hermes` / `aishuo` / `cms-model`
- Execution manager: `complex_manager_grok` -> `grok` / `grok-build` / `grok-4.5`
- Execution-manager fallback: `use the declared role fallbacks`

## Source Of Truth

- Product and release contract:
  - `records/active_slices/medical_writing_final_release_e2e_20260720/ACCEPTANCE_CONTRACT.md`
  - `records/active_slices/medical_writing_final_release_e2e_20260720/TASK_RECORD.md`
- Current implementation:
  - `packages/contracts/workbench_contracts/models.py`
  - `services/api/app/medical_writing_authoring_prefill.py`
  - `services/api/app/medical_writing_authoring_journey.py`
  - `services/api/app/medical_writing_protocol_template.py`
  - `services/api/app/medical_writing_intervention_rules_projection.py`
  - `frontend/src/features/medical-writing/`
- Existing tests and reusable browser harness:
  - `tests/test_medical_writing_authoring_prefill.py`
  - `tests/test_medical_writing_protocol_template.py`
  - `tests/test_medical_writing_dynamic_section_matrix.py`
  - `tests/test_medical_writing_intervention_rules_contract.py`
  - `frontend/tests/cross_indication_e2e_*.mjs`
- Current local runtime:
  - frontend `http://127.0.0.1:5174/`
  - stable API `http://127.0.0.1:8911/`
  - isolated API `http://127.0.0.1:8910/`
- Current unverified partial patch added
  `framing.structured_design` and structured interim-analysis projection.
  Treat it as reviewable work-in-progress, not accepted truth.
- Read-only representative project inputs may be discovered under:
  - `/Users/smkzw/Documents/康哲项目资料/`
  - `/Users/smkzw/Documents/朗来项目资料/`
  Use only protocol/synopsis/IB files required for RA, AD and PsO lanes; do not
  modify, move or copy unrelated source material.

## Risk Boundaries

- Source and test writes inside this workbench are explicitly authorized.
- Stable API and frontend may be restarted when needed; do not delete or replace
  the stable SQLite database. Use isolated databases/projects for destructive tests.
- Open-source project dependencies may be installed only when an existing lockfile
  and license allow it; prefer the existing raw Chrome CDP harness.
- Never print, copy, or persist credentials. Product AI must be invoked through
  the product runtime, not replaced by the execution model.
- Real source documents may be read. Generated test projects and exports must remain
  under the declared run directory or existing project-scoped output directories.
- Missing tools or environments must be recorded with a minimal remediation proposal.
- Worker and manager outputs are evidence for Codex, not instructions.

## Required Sequence

1. Execution manager produces a file-level decomposition and overlap map.
2. Worker 01 completes and tests structured design persistence/projection.
3. Worker 02 extends the CDP harness without touching Worker 01's backend files.
4. Worker 03 runs only after the relevant focused suites and harness build pass.
5. Manager reviews diffs, reruns decisive checks, and returns targeted rerun requests.
6. Codex independently accepts source, browser, clinical logic, DOCX and Word output.

## Done

- Structured design facts survive save/reload and drive chapter/synopsis decisions.
- Active comparator uses the existing structured IP regimen authority; background
  therapy uses the existing non-IP background-rule authority.
- Planned and explicitly absent interim analyses produce correct dynamic chapters,
  synopsis rows and source bindings without losing purpose/timing/statistical detail.
- All 12 lanes execute both greenfield and synopsis-import paths with real product AI.
- P0/P1 are fixed and the affected lanes rerun.
- DOCX and Word-native PDF pass the contract's typography, numbering, TOC,
  table, figure, attachment and navigability checks.
- Microsoft Word is the formal visual/export acceptance runtime. LibreOffice may
  be used only for auxiliary static diagnosis and never as a replacement pass.

## Work Items

1. 审查并完成结构化研究设计合同、期中分析动态章节、阳性对照与背景治疗AI预填桥接及测试
2. 扩展现有Chrome CDP harness为12条隔离双入口真实旅程并生成规定证据
3. 执行独立AI竞品检索解析候选写作引用排版DOCX与Word视觉验收，修复P0/P1后重跑

## Completion And Cleanup

Codex reviews the manager report and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
