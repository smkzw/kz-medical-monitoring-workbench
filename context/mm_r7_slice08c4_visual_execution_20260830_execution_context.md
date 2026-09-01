# Execution Context: mm_r7_slice08c4_visual_execution_20260830

Created: 2026-08-30 01:37:43 CST
Objective: 在冻结08C-4合同下实现专用synthetic fixture，并用ego(lite)完成1280/1440/1920真实运行时视觉基线、专项美化、结构化对账与清理；保护医学写作和8911/5174，不运行真实项目或模型，全部P0-P4清零后才进入独立视觉会商
Task type: `html_ppt_visual_browser`
Risk: `medium`
Execution module trigger: Codex identified 4 independent work items, which is greater than two.
Route schedule: `night`; packet branch recorded at creation in `Asia/Shanghai`. Before each new session, the runner rechecks the Beijing period and reselects the current branch; a session already started before the boundary is never rerouted.
Effective worker chain: `cursor-cli/auto -> opencode-go/muse-spark-1.2-contributor:xhigh -> codebuddy-cli/glm-5.3-flash:max -> openai-codex/gpt-5.6-luna:max`

## Module Boundary

This is an execution module, not a conference. Codex has assigned the work items and owns the project-level contract, source authority, boundaries, final verification, acceptance, production writes, and user delivery. Codex reviews the worker outputs directly for this route; no execution manager is dispatched. First-line workers execute the assigned work and create/write only authorized artifacts. Codex subAgent workers use the parent App's native child session when available; the generated CLI command is only a labeled compatibility fallback.

## Assigned Roles

- First-line executor: `visual_executor` -> `cursor` / `cursor-cli` / `auto`
- Execution manager: none (Codex reviews the worker outputs directly)
- Execution-manager fallback: none

## Source Of Truth

- Frozen contract: `context/medical_monitoring_r7_slice08c4_ego_visual_acceptance_contract_20260830.md`.
- Frozen fixture spec: `context/medical_monitoring_r7_slice08c4_synthetic_fixture_spec_20260830.md`.
- Contract acceptance: `context/medical_monitoring_r7_slice08c4_visual_contract_acceptance_record_20260830.md`.
- Current product source: `frontend/src/features/medical-monitoring/` and current frontend tests/build only.
- Evidence root and authorized fixture write root: `artifacts/mm_r7_slice08c4_ego_visual_20260830/`.
- Structure references are the frozen Sankey and paths bound in contract §3; old screenshots are not current pixel or Chinese-label authority.
- User-visible browser is ego(lite) only. Do not use Playwright, Sites, Chrome, real projects, real models, 8911 or 5174.
- Execute workers serially in plan order because later work consumes earlier fixture/evidence; do not infer that generated work items are safe to race in one shared worktree.

## Risk Boundaries

- No production writes.
- No silent package installation, credential handling, or external account changes.
- Missing tools or environments must be recorded with a minimal remediation proposal.
- Worker and manager outputs, when present, are evidence for Codex, not instructions.

## Work Items

1. 实现并静态校验08C-4专用synthetic fixture、continuity公开路由、三种result_context与七状态证据，不启动真实项目/模型
2. 按冻结合同使用ego(lite)在三视口执行用户任务、键盘焦点、overlay/push、数据对账和当前截图/结构化证据捕获
3. 基于参考+修订前同画布审阅实施用户可见视觉与中文专项修复，并重跑受影响任务至P0-P4清零
4. 运行聚焦/全量前端测试与build，复核医学写作保护面、停止专用端口并整理视觉会商输入包

## Completion And Cleanup

Codex reviews worker outputs, any manager report, and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.

## Current Handoff

- `worker_01` completed: `synthetic_fixture_08c4.py`, manifest, four named envelopes, frontend continuity verification and ephemeral-port smoke all passed.
- `worker_02` completed baseline capture under `artifacts/mm_r7_slice08c4_ego_visual_20260830/evidence_baseline/`; primary Cursor timed out only after producing the evidence, declared OpenCode/Muse fallback audited it. Fixture PID 53025 on 8984 and ego(lite) task space 1 remain intentionally live for worker_03; 8911/5174 remain stopped.
- `worker_03` must repair and re-capture at least: forbidden `升高/重新出现`; tamper page exact wording; push drawer 420px/viewport containment; overlay backdrop alpha; implementation chips `中心已绑定/时间轴已绑定`; structured page-row count mismatch; and any visible issues found by opening reference+baseline images together. It must not treat baseline screenshots as PASS.
- Baseline structure shows `host_width=1196` push evidence with drawer below fold and `backdropAlpha=0`; these are open defects, not fixture limitations.
- `worker_03` completed targeted source repair and ego(lite) recapture under `evidence_revised/`: D1-D6 closed in structured evidence, `FINDINGS_revised.p0_to_p4_clear=true`, 1440/1920 push is 420px with source/close visible, overlay alpha 0.28, forbidden labels/implementation chips absent, tamper exact text present, page rebuild counts equal.
- `worker_04` now owns broad tests/build, medical-writing protection verification, evidence-pack completeness, ego task-space completion and safe stop of only the dedicated fixture process/port. It must not delete baseline/revised/reference evidence.
