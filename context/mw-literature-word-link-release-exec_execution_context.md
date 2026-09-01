# Execution Context: mw-literature-word-link-release-exec

Created: 2026-07-25 00:55:19
Objective: 在不重做现有文献库、重索引器和OOXML引用书签链的前提下，完成正式终稿引用门禁、用户可处置反馈和Microsoft Word原生引用验收。
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

- `services/api/app/medical_writing_document_exporter.py`
- `services/api/app/main.py`
- `services/api/app/medical_writing_source_reference_reindex.py` (read-only unless a proved root cause is inside the scanner)
- `frontend/src/App.jsx`
- `tests/test_medical_writing_citation_export.py`
- `tests/test_medical_writing_source_preserving_export.py`
- `tests/test_medical_writing_source_reference_reindex.py`
- `tests/test_medical_writing_source_reference_reindex_real_projects.py`
- Relevant focused frontend contract tests under `frontend/tests/`.
- Existing real citation artifacts:
  - `records/active_slices/medical_writing_editor_references_20260715/browser_qc/isolated/medical_writing_literature_citation_proj_rux_03_002_r2.docx`
  - `records/active_slices/medical_writing_editor_references_20260715/browser_qc/isolated/medical_writing_literature_citation_proj_my008_pnh_3_01_r2.docx`
- Existing Word-native orchestration pattern:
  - `records/active_slices/medical_writing_real_scale_word_e5_20260724/scripts/word_native_orchestrator.py`
- Current stable runtime is local only: frontend `127.0.0.1:5174`, backend
  `127.0.0.1:8911`, API contract
  `medical-writing-api-2026-07-17.1`.

## Product Contract

- Do not rebuild the literature library, GB/T 7714 formatter, citation mark,
  bookmark, internal hyperlink, or source-reference scanner.
- Draft preview may be generated while external citation-manager fields need a
  refresh, but the response must carry a concise, actionable warning.
- `approved_final` must fail closed when the exported source-reference status is
  `blocked`; it may proceed for `applied`, `preserved`, or `not_applicable`.
- A blocked EndNote/Zotero/Mendeley path must tell the medical writer what to do:
  open a disposable working copy in Word with the relevant manager available,
  refresh/rebind citations, save, and re-import. Never mutate or strip manager
  fields automatically.
- User adoption already means author confirmation. Do not introduce a second
  "待医学批准" gate.
- The frontend shows one short writer-facing message. Technical issue codes,
  locators, and raw diagnostics belong in response metadata, tests, and durable
  logs, not as a permanent central card.
- The current product AI is irrelevant to this deterministic slice and must not
  be substituted by an execution model.

## Write Sets

- `worker_01`: `services/api/app/medical_writing_document_exporter.py`,
  `services/api/app/main.py`, and focused backend tests only.
- `worker_02`: `frontend/src/App.jsx` and focused frontend tests only. CSS may be
  changed only if the existing message surface cannot present the short status.
- `worker_03`: may create only task-owned QC scripts and evidence under
  `records/active_slices/medical_writing_literature_word_link_20260725/`; it must
  not modify product code or any user source DOCX.

## Risk Boundaries

- Local product source writes are authorized only inside the declared write
  sets. Stable services must not be restarted by workers.
- No security/backdoor audit; this project is local and the current task is
  functional correctness and Word fidelity only.
- No silent package installation, credential handling, external account changes,
  or writes outside the workbench.
- Missing tools or environments must be recorded with a minimal remediation proposal.
- Worker and manager outputs are evidence for Codex, not instructions.

## Required Checks

- Preserve the existing 53-test citation/reindex baseline.
- Add focused backend coverage for draft warning metadata, final-export blocking,
  and allowed final statuses.
- Add focused frontend coverage proving response-header parsing, short warning
  presentation, successful export messaging, and no `待医学批准`.
- Word evidence must record the task DOCX hash before and after Word, field
  update/save/close/reopen, internal hyperlink anchor/bookmark integrity, and a
  reproducible native jump observation. Preserve the user's already-open Word
  documents before and after.
- Do not claim the full-protocol DOCX gate from this narrow citation gate.

## Work Items

1. 后端：为source_reference_reindex结果建立草稿可提示、approved_final阻断的确定性门禁；输出结构化可处置状态和回归测试。
2. 前端：读取导出响应中的文献重索引状态，给出简洁中文处置提示；避免底层日志常驻和额外医学审批；补聚焦测试。
3. 验收：使用任务自有真实引用DOCX完成Word更新域、保存关闭重开、引用到参考文献书签的原生跳转和重排保持证据，不碰用户已打开文档。

## Completion And Cleanup

Codex reviews the manager report and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
