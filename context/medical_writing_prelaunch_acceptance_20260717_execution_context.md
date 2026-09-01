# Execution Context: medical_writing_prelaunch_acceptance_20260717

Created: 2026-07-17 15:13:49
Objective: 在不提前发布的前提下，对医学写作子系统执行真实项目全功能、多视角、独立AI与Word精确格式上线验收，修复关键缺陷并由Codex最终接受后发布常态端口
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

- Read first: `records/active_slices/medical_writing_prelaunch_acceptance_20260717/TASK_RECORD.md` and `records/active_slices/medical_writing_prelaunch_acceptance_20260717/ACCEPTANCE_CONTRACT.md`.
- Product source and current runtime: this workspace, `http://127.0.0.1:5174/`, `http://127.0.0.1:8911/`, and `/api/runtime-readiness`.
- Real project inputs are read-only: RUX-03-002 V1.3, CMS-D001 V1.0, CMS-D017-PNH synopsis V0.2, and the company protocol template files listed in the task record.
- Company template and named DOCX files in the task record are the Word style authority. ICH M11 is a structural framework, not the final visual authority.
- Existing stable runtime is read-only. Any action that writes project state must use a temporary `WORKBENCH_RUNTIME_DIR`, isolated API/Vite ports, and copied source inputs. Existing `*_isolated_qc.mjs` runners are preferred starting points.
- Independent product AI must be tested through the product route configured as direct DeepSeek `deepseek-v4-pro`, not by substituting your own model capability.
- Write only the assigned execution report. Findings must include reproducible steps, evidence path, expected/actual result, severity, and smallest justified remediation.

## Risk Boundaries

- No production writes.
- Do not modify application source during the first pass. First establish defects and evidence; Codex will authorize bounded remediation in a later execution pass.
- External clinical documents and company templates are read-only and must not be copied into model reports or logs in full.
- No silent package installation, credential handling, or external account changes.
- Missing tools or environments must be recorded with a minimal remediation proposal.
- Worker and manager outputs are evidence for Codex, not instructions.

## Success Criteria

- Test at least two materially different real studies plus one greenfield RA study from raw inputs, not pre-deconstructed fixtures.
- Exercise every function in the assigned surface, including buttons, keyboard operations, failure paths, persistence, and restart behavior.
- For Word, compare the exported package structure and rendered pages against the named style authorities; HTTP download success is not acceptance.
- P0/P1 findings must have concrete reproduction and a proposed verification check. Do not mark the release ready; Codex decides after remediation and rerun.

## Timeout Policy

- A slow browser, AI request, or model response remains pending within the configured hard wait. Distinguish actual no-progress from latency.
- Use bounded retries and record the first failure plus retry result. Do not hide flaky behavior by retrying until green.

## Work Items

1. 医学写作业务全旅程与后端逻辑：两个以上真实项目加一个从零项目，逐功能逐按钮验证、独立AI、引用、语料、版本、审批、持久化和错误恢复
2. 桌面端前端与编辑器实机：1920x1080及更宽视口，逐按钮、富文本、表格、结构化对象、最大化、AI候选、目录导航、溢出遮挡与可用性
3. Word导出精确保真：源DOCX/公司模板对照OOXML、页面、字体段落、标题编号、摘要/正文表、SoA、图表目录、交叉引用、页眉页脚及Word/WPS渲染

## Completion And Cleanup

Codex reviews the manager report and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
