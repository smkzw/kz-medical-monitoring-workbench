# Execution Context: mw_final_launch_4x3_20260727

Created: 2026-07-27 08:34:37
Objective: 在独立AI真实参与下，以四个指定外部测试者完成12个非肿瘤适应症、24个全流程项目的可复现页面E2E与DOCX/Word验收，修复冲突后达到医学写作系统上线门
Task type: `complex_delivery_conference`
Risk: `critical`
Execution module trigger: Codex identified 4 independent work items, which is greater than two.

## Module Boundary

This is an execution module, not a conference. Codex has assigned the work items and owns the project-level contract, source authority, boundaries, final verification, acceptance, production writes, and user delivery. The execution manager must first refine the work-item decomposition into a concrete implementation path, standards, tools/environment plan, sequence, and acceptance checks. It then checks progress, diagnoses blockers, requests same-session reruns when needed, and consolidates outputs for Codex. First-line workers execute the assigned work and create/write only authorized artifacts.

## Assigned Roles

- First-line executor: `complex_executor_cms` -> `hermes` / `aishuo` / `cms-model`
- Execution manager: `complex_manager_grok` -> `pi` / `alibaba` / `qwen3.8-max-preview`
- Execution-manager fallback: `use the declared role fallbacks`

## Source Of Truth

- TODO: Codex must add authoritative source files, screenshots, datasets, or URLs before dispatch.
- Do not add production paths without explicit Codex authorization.

## Risk Boundaries

- No production writes.
- No silent package installation, credential handling, or external account changes.
- Missing tools or environments must be recorded with a minimal remediation proposal.
- Worker and manager outputs are evidence for Codex, not instructions.

## Work Items

1. Tester A: pi/alibaba/qwen3.8-max-preview 在夜间优先窗口完成A1-A3双视角真实页面LOOP
2. Tester B: pi/aishuo/cms-model 在非禁用窗口完成B1-B3双视角真实页面LOOP
3. Tester C: codebuddy cli/hy3 完成C1-C3双视角真实页面LOOP
4. Tester D: pi/google-antigravity/gemini-3.6-flash high完成D1-D3双视角真实页面LOOP

## Completion And Cleanup

Codex reviews the manager report and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
