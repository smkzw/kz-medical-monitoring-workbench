# Task Context: mm_r8_gate3_notification_decision_contract_20260831

Created: 2026-08-31 12:38:03
Objective: 在已接受 R8 G2 基础上复盘并冻结 G3 NOTIFICATION_DECISION_LOCKED：依据用户已确认的后台运行与懒惰/视觉敏感/中文原生监察员画像，选择并定义离页完成/失败可见路径，冻结 project_ref+admission_id+run_id 路由、幂等、终态、权限/不可用降级、中文可行动文案、点击只导航不启动分析、G5/G6 验收边界及 G4 后续顺序；只做 synthetic/offline 合同与计划，不改产品、不启动服务/浏览器/模型、不访问真实项目或医学写作。
Task type: `stage_review_plan`
Risk: `medium`
Selected agent route: `codex` / `gpt-5.6-sol` / `medium`

## Preferred Browser Advisory

- Role: `chatgpt-web-pro-advisory` via `codex-with-chatgpt`.
- Assignment: preferred stage-level retrospective and phase-planning adviser.
- UI selection: `Pro` / `GPT-5.6 Sol`; verify the visible ChatGPT UI state on each new conversation.
- Boundary: read-only MCP advisory; it is not dispatchable through the runner and has no automatic callback. Reuse the same C2C session and observe completion in the foreground in-app-browser tab.
- If no valid complete response is observed, continue the executable route below; do not silently turn the browser role into a subprocess route.


## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `reviews/medical_monitoring_r8_gate0_source_admission_anti_overfit_contract_v0_1_20260831.md` §§8.2、9：Path A/B 正式定义与 G3 有序门禁。
- `context/medical_monitoring_r8_gate2_synthetic_runtime_acceptance_record_20260831.md`：G2 已接受边界、未接受项与下一安全动作。
- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md`：R7 后台任务/本地通知需求与当前 R8 恢复锚点。
- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md` §§15.1–15.4：本地应用、审计、备份与迁移边界。
- `context/mm_r7_phase_closure_review_20260831_conference_context.md`：R7 收口时对本地通知/一键应用缺口的显式继承。
- `frontend/src/App.jsx:1446` 与 `frontend/src/features/medical-monitoring/r7/MedicalMonitoringR7ProgressPanel.jsx:116`：当前仅有未开放的通知中心入口和页面内运行状态。

## Scope

- In scope: 复盘 G2→G3 阶段边界；在 Path A/B 中作出一个可追溯决定；冻结通知身份、终态、幂等、能力/权限降级、点击导航、中文用户表达、G4/G5/G6 顺序与验收边界。
- Out of scope: 修改产品源码；启动服务、端口、浏览器或模型；访问五个真实项目；修改医学写作子系统；证明真实通知送达、真实用户可见、医学质量或 §15.4 已通过。

## Success Criteria

- 合同明确选择 G0 定义的 Path A，且不把应用内持久记录误称为 Path B。
- 每个通知事实完整绑定 `project_ref + admission_id + run_id`，点击只导航、不启动/重试分析。
- 原样保留上游终态；只有 `analysis_complete` 且结果可访问时可发完成通知，其他终态使用准确中文，不折叠为泛化“失败”。
- 授权/拒绝/不可用/未知四类能力状态均有 fail-closed 处置；通道失败不改写分析终态，不声称用户已看到。
- 合同显式区分 G3 决策、G4 实施、G5 synthetic/offline 合同验收与 G6 synthetic ego(lite) 受众可见验收。
- 独立审阅关闭 P0/P1；在此之前不得进入 G4。

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.
- A provider catalog/auth/transport preflight is diagnostic, not a live capability verdict: timeout, auth refresh failure, malformed output, or a stale/incomplete catalog must be recorded and followed by one real route attempt. Explicit user-selected routes are not blocked merely because the catalog does not list them; only a missing executable or native transport boundary may stop before that attempt.

## Loop Log

- 2026-08-31 12:38:03: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-31: fresh-context Codex subAgent 完成阶段审阅；其 capability/identity/idempotency/fail-closed 建议可用，但将“应用内持久降级”误称为 G0 Path B，且将上游终态过度折叠为 completed/failed；父 Codex 依 G0 §8.2 和 §3.3 纠正，经独立会商两轮修订形成 `reviews/medical_monitoring_r8_gate3_notification_decision_contract_v0_3_20260831.md`。
