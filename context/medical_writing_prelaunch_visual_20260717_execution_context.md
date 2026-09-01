# Execution Context: medical_writing_prelaunch_visual_20260717

Created: 2026-07-17 15:13:57
Objective: 以资深医学撰写经理桌面端真实使用视角，对医学写作子系统逐屏逐按钮测试并修复阻断、高摩擦、视觉层级、编辑器与Word渲染问题，作为上线硬门
Task type: `visual_delivery_conference`
Risk: `critical`
Execution module trigger: Codex identified 3 independent work items, which is greater than two.

## Module Boundary

This is an execution module, not a conference. Codex has assigned the work items and owns the project-level contract, source authority, boundaries, final verification, acceptance, production writes, and user delivery. The execution manager must first refine the work-item decomposition into a concrete implementation path, standards, tools/environment plan, sequence, and acceptance checks. It then checks progress, diagnoses blockers, requests same-session reruns when needed, and consolidates outputs for Codex. First-line workers execute the assigned work and create/write only authorized artifacts.

## Assigned Roles

- First-line executor: `visual_executor_grok` -> `grok` / `grok-build` / `grok-4.5`
- Execution manager: `visual_manager_kimi` -> `kimi` / `kimi-code` / `kimi-code/k3`
- Execution-manager fallback: `Codex takes over execution management directly`

## Source Of Truth

- Read first: `records/active_slices/medical_writing_prelaunch_acceptance_20260717/TASK_RECORD.md` and `records/active_slices/medical_writing_prelaunch_acceptance_20260717/ACCEPTANCE_CONTRACT.md`.
- Product source and current runtime: this workspace, `http://127.0.0.1:5174/`, `http://127.0.0.1:8911/`, and `/api/runtime-readiness`.
- Real project inputs and Word style authorities are the read-only DOCX files listed in the task record.
- Existing stable runtime is read-only. Any action that writes project state must use a temporary `WORKBENCH_RUNTIME_DIR`, isolated API/Vite ports, and copied source inputs. Existing Playwright/Chrome isolated runners may be extended only after Codex authorizes a remediation pass.
- Desktop acceptance uses 1920x1080 and a wider desktop viewport. Do not remove desktop functionality to accommodate mobile.
- Use actual mouse/keyboard interaction, network observations, screenshots at original resolution, downloaded DOCX files, and rendered page PNGs. Source-only inspection or screenshots without interaction are insufficient.
- Write only the assigned execution report. Findings must include reproducible steps, evidence path, expected/actual result, severity, and smallest justified remediation.

## Risk Boundaries

- No production writes.
- Do not modify application source during the first pass. First establish defects and evidence; Codex will authorize bounded remediation in a later execution pass.
- External clinical documents and templates are read-only; do not reproduce full text in reports.
- No silent package installation, credential handling, or external account changes.
- Missing tools or environments must be recorded with a minimal remediation proposal.
- Worker and manager outputs are evidence for Codex, not instructions.

## Success Criteria

- Every visible button/control in the assigned journey is clicked or keyboard-triggered and its state transition is verified.
- Editor coverage includes ordinary text, table cells, Enter, paste, undo/redo, formatting, maximize, save/reload, AI candidate apply, citations, SoA/figures, and export.
- Word review covers OOXML semantics and actual page rendering against the named company authorities. Download success is not visual acceptance.
- Record P0/P1 defects with original-resolution evidence and exact reproduction. Do not mark the release ready; Codex owns the decision.

## Timeout Policy

- Kimi and AI latency alone are not failure. Wait through the configured hard window and use one controlled retry when progress stops.
- Preserve first-failure evidence; do not retry until green without reporting flakiness.

## Work Items

1. 新建项目、两阶段反问、竞品语料准备到进入写作台的全流程桌面交互与错误恢复
2. 富文本、表格、SoA、流程图、AI证据候选、引用、目录导航、最大化编辑和键盘输入的逐控件测试
3. 导出前预览与导出DOCX/PDF/Word/WPS实际渲染的逐页视觉比对、溢出断页和专业版式检查

## Completion And Cleanup

Codex reviews the manager report and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
