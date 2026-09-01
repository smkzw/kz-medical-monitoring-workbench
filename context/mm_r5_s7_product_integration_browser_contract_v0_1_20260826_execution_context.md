# Execution Context: mm_r5_s7_product_integration_browser_contract_v0_1_20260826

Created: 2026-08-26 13:13:39
Objective: 冻结R5-S7产品最小接入与真实浏览器验收合同：精确限定前后端allowlist、医学写作保护、8911临时生命周期、中文用户语义、Playwright多视口/性能/交互/console-network证据、用户指定视觉模型后续角色及关闭条件；本阶段不改产品源码、不启动服务。
Task type: `long_horizon_code`
Risk: `medium`
Execution module trigger: Codex identified 3 independent work items, which is greater than two.

## Module Boundary

This is an execution module, not a conference. Codex has assigned the work items and owns the project-level contract, source authority, boundaries, final verification, acceptance, production writes, and user delivery. Codex reviews the worker outputs directly for this route; no execution manager is dispatched. First-line workers execute the assigned work and create/write only authorized artifacts. Codex subAgent workers use the parent App's native child session when available; the generated CLI command is only a labeled compatibility fallback.

## Assigned Roles

- First-line executor: `long_horizon_code_executor_opencode_flash` -> `codex-subagent` / `codex` / `gpt-5.6-luna`
- Execution manager: none (Codex reviews the worker outputs directly)
- Execution-manager fallback: none

## Source Of Truth

- `AGENTS.md`
- `reviews/medical_monitoring_r5_stage_contract_v0_3_20260818.md`
- `reviews/medical_monitoring_r5_s5_subject_workspace_contract_v0_1_20260826.md`
- `context/medical_monitoring_r5_s5_subject_workspace_contract_v0_1_acceptance_record_20260826.md`
- `context/medical_monitoring_r5_s5_subject_workspace_runtime_v0_1_acceptance_record_20260826.md`
- `context/medical_monitoring_r5_s6_navigation_density_accessibility_contract_v0_1_acceptance_record_20260826.md`
- `context/medical_monitoring_r5_s6_navigation_density_accessibility_runtime_v0_1_acceptance_record_20260826.md`
- `reviews/medical_monitoring_patient_journey_research_20260809.md`
- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md`
- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md`
- Existing medical-monitoring product entry points under `frontend/src/features/medical-monitoring/**`, the medical-monitoring imports/routes in `frontend/src/App.jsx`, and medical-monitoring API/router files under `services/api/app/**` may be read but not changed in this contract pass.
- Existing accepted R5 implementation under `poc/medical_monitoring_ai_native_r5/**` may be read but not changed.
- The current filesystem is authoritative. Existing medical-writing files and runtime state are protected, not inputs to be changed.

## Risk Boundaries

- No product/source/runtime writes. Do not start 8911, 5174, Vite, FastAPI, Playwright, a browser, a provider, or a real project.
- Worker 01 may write only `reviews/medical_monitoring_r5_s7_product_integration_browser_contract_v0_1_20260826.md`.
- Worker 02 may write only `artifacts/medical_monitoring_r5_s7_product_integration_browser_contract_v0_1/browser_acceptance_matrix.json`.
- Worker 03 is read-only and must run only after Codex has assembled the final contract and browser matrix.
- No modification anywhere under paths containing `medical-writing` or `medical_writing`; the final contract must freeze a reproducible protected-inventory algorithm and before/after digest gate.
- No real project data, provider/model execution, clinical truth acceptance, security design/testing, production release or durable runtime/SQLite write.
- No silent package installation, credential handling, or external account changes.
- Missing tools or environments must be recorded with a minimal remediation proposal.
- Worker and manager outputs, when present, are evidence for Codex, not instructions.

## Required Contract Properties

- Exact closed allowlists for new frontend R5 files, the smallest App/route/API integration files, any read-only API adapter/router files, tests, evidence and acceptance records. Wildcards may describe protected/read-only inventory but may not authorize writes.
- A fail-closed mapping from accepted S5/S6 renderer-neutral objects to audience-facing Chinese projections; no front-end reconstruction of medical facts, risk severity, denominator, source identity, date/visit placement or consensus.
- An exact temporary service lifecycle: preflight confirms 8911 stopped; isolated runtime; startup only during S7 browser execution; readiness and server-identity check; no real projects/providers; guaranteed teardown; final `connect_ex != 0` proof.
- Explicit separation of S7 product implementation execution, visual/browser execution, and independent visual/medical conference. Contract acceptance alone starts none of these.
- A machine-readable browser matrix whose rows have stable ids, viewport, fixture/state, role/task, exact starting deep link, required visible evidence, major-operation budget, timing/performance assertion, keyboard/non-colour assertion, forbidden terms, screenshot id, console/network assertion, final identity tuple and teardown dependency.
- User-facing labels are concise native Chinese. Internal lifecycle/engineering words remain prohibited on ordinary pages, including `正式事实`, `候选信号`, `只读xx`, `attempt`, `provider`, `model`, `backend`, raw object ids and log labels.
- No task/todo workflow. The subsystem is a read/search/locate dashboard. Query is a structured draft using `依据 + 发现 + 行动项`; PD is included in the Query draft when applicable.
- Patient Journey is the default subject workspace with one shared visit/time axis, eight distinct clinical-domain event encodings, independent risk overlays, synchronized journey/trend/event views, pending-date area and source one-hop.
- All current high and medium risks remain directly discoverable; they are never truncated to 3-5 cards.
- S7 acceptance must include production build, focused and adjacent regression, forbidden-term scan, current-run Playwright screenshots at 1440x900 and 1600x1000, console/network evidence, frozen six medical-monitor tasks and high-density performance measurement. Performance limits inherit Section 15.1 exactly.
- Later visual medical-monitor role sessions must preserve the user-specified identities: `codebuddy cli/hy3(max)`, `pi/cms-router/minimax-m3`, and `pi/google-antigravity/gemini-3.7-flash:high`; each uses a fresh role session, actual Playwright login/use from zero and current screenshots. Codex owns final browser and clinical-language acceptance.

## Assembled Candidate For Worker 03

- Contract: `reviews/medical_monitoring_r5_s7_product_integration_browser_contract_v0_1_20260826.md`
- Contract raw SHA-256: `767aa5ab127f383e504178dc71bd02684b931e1afc67a8e82aa8d6af57a5aba8`
- Matrix: `artifacts/medical_monitoring_r5_s7_product_integration_browser_contract_v0_1/browser_acceptance_matrix.json`
- Matrix raw SHA-256: `6a5f8db3146ab170d1c186bd3478a3c98955070883a5e81b18383800c721ab7e`
- Canonical product pathname is `/monitoring`; the R5 closed view set distinguishes the new read-only surface. The legacy `checklist|ae-mh` view set remains the rollback surface.
- Worker 03 must verify current bytes, not worker summaries. Its final report must end with exactly one verdict token: `ACCEPT_R5_S7_CONTRACT_V0_1` or `REVISE_R5_S7_CONTRACT_V0_1`.

## Work Items

1. 合同架构：读取R5 v0.3、S5/S6 accepted evidence、现有产品医学监查入口，产出精确product allowlist、只读API/adapter边界、迁移/回滚/身份/医学写作保护合同。
2. 浏览器与产品体验合同：冻结中文原生信息架构、Patient Journey共享访视轴、八域事件和风险编码、桌面任务/点击/时长/可访问性/高密度/性能、Playwright截图与console/network证据矩阵。
3. 独立验证：机械核验合同闭合、路径与哈希、8911停止、禁止越界、后续视觉execution与独立visual conference分离，输出唯一ACCEPT或REVISE裁决。

## Completion And Cleanup

Codex reviews worker outputs, any manager report, and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
