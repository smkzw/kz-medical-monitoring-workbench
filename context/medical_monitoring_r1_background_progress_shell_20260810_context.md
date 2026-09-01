# Task Context: medical_monitoring_r1_background_progress_shell_20260810

Created: 2026-08-10 00:50:59
Objective: 在隔离 synthetic R1 中建立后台医学监查 facade 与中文进度界面 shell，只读消费已接受 audience projection，验证离开页面后继续运行、刷新恢复、权威数字进度和结构化工作播报，不启动产品服务、8911或真实项目
Task type: `html_ppt_visual_browser`
Risk: `medium`
Selected agent route: `alibaba` / `qwen3.8-max` / `xhigh`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md` 第 11.4、12 节：受试者医学旅程、后台运行、真实数字进度、结构化播报和中文受众语言合同。
- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md` 的 R1 步骤 7、完成证据与当前恢复点。
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/audience_progress.py`：已验收的受众进度唯一投影边界。
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/controller.py`、`capability_runtime.py`、`store.py`：已验收的应用控制器、attempt journal 与 manifest work-unit 权威状态。
- `poc/medical_monitoring_ai_native_r1/docs/R1_AUDIENCE_PROGRESS_EVIDENCE.md` 与 `R1_CONTROLLER_BINDING_EVIDENCE.md`。
- `poc/medical_monitoring_ai_native_r1/slices/aemh_audience_workbench/` 与 `slices/patient_journey/`：已验收的中文视觉契约和浏览器测试惯例。
- 当前文件系统、synthetic/offline 测试与真实浏览器渲染是本切片最终事实。

## Scope

- In scope:
  - 建立一个框架中立、进程内持久的后台作业 facade；一次启动后即使无浏览器轮询也继续处理 synthetic work units。
  - 作业进度只能通过 `project_audience_progress(store, run_id)` 读取；不得在 facade 或前端另存 completed/total/percent 状态机。
  - 建立中文进度界面 shell：总进度、阶段进度、当前正在处理、最新动态、离开后继续和返回/刷新后恢复。
  - 用标准库或已有依赖提供隔离 demo；浏览器验证如需 HTTP，仅可使用 `127.0.0.1:0` 分配的临时端口，测试结束必须关闭。
  - 聚焦测试、相邻回归、真实浏览器/视觉检查和隔离失败/恢复测试。
- Out of scope:
  - 产品源码、医学写作子系统、五个真实项目、真实 provider/harness/API 与 8911。
  - 后台进程在整个应用关闭/设备重启后存活；本切片只证明页面导航、断开轮询、刷新与 facade 重建时从 SQLite 重建受众视图。
  - 新的 graph scheduler、第二套进度台账、新 UI 框架、真实临床结论或 R1 总体验收。

## Success Criteria

- 关闭前端轮询或离开进度页后，后台 work unit 继续从 pending 推进到终态；重新打开页面时显示 SQLite 当前真实进度。
- 界面 completed/total/percent、各阶段数字、当前工作和动态逐项与 `project_audience_progress` 返回值一致；不能由时间、动画或前端估算进度。
- 前端消费一个明确的白名单 audience schema，不可读取或展示 run/node/attempt/provider/model/backend/hash/log/manifest revision 等内部身份。
- 用户可明白看到“可离开此页，医学监查将在后台继续”、当前处理内容和最新动态；页面不出现“正式事实”“候选信号”“只读xx”“后端标识”等工程语言。
- 运行失败/受阻不写成成功；刷新、重复连接和多客户端读取不得重复执行作业。
- 聚焦、audience-progress/controller 相邻、R1 core、前端契约、真实浏览器和 scoped Ruff/compile 验证通过；独立新上下文 reviewer 决定本切片是否接受。

## Risk Boundaries

- Allowed writes are limited to:
  - `poc/medical_monitoring_ai_native_r1/src/mm_r1/background_progress.py`
  - `poc/medical_monitoring_ai_native_r1/slices/background_progress_shell/**`
  - `poc/medical_monitoring_ai_native_r1/tests/test_background_progress.py`
  - this task's `context/`, `prompts/`, `reviews/`, `metrics/`, `runs/` and one R1 evidence file.
- Existing accepted runtime/controller/store/audience-progress and existing UI slice sources are read-only references in the delegated implementation round.
- Do not add network/package dependencies. Do not bind to a fixed port. Never start or kill 8911.
- Synthetic fixture text must be fictional and contain no real project/patient material.
- UI server/facade is an isolated POC integration seam, not a production local-server decision.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.
- A provider catalog/auth/transport preflight is diagnostic, not a live capability verdict: timeout, auth refresh failure, or malformed probe output must be recorded and followed by one real route attempt. Only a missing executable or explicit invalid/retired/unlisted model may stop before that attempt.

## Loop Log

- 2026-08-10 00:50:59: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-10 02:22: Worker completed the bounded implementation. Codex did not accept its self-review; direct reproduction found three facades could perform 24 real callbacks while the ledger showed eight terminal items, and browser inspection found stage bars and status tones needed correction.
- 2026-08-10 02:37: Main venue corrected process-local normal-path serialization, exact ratio rendering and Chinese/status presentation, then froze the review packet and initialized independent acceptance.
- 2026-08-10 02:46: Independent reviewer returned VETO on a distinct Store fault window: the real action could complete, the terminal write could fail, and the worker would silently die before a later facade repeated the action.
- 2026-08-10 02:55: Main venue added worker-level error capture and continuation, passed a stable idempotency key into the action callback, documented at-least-once recovery semantics and added fault-injection coverage. The same reviewer session returned ACCEPT.
- 2026-08-10 03:07: Current-filesystem verification completed: focused 12, R1 core 285, AE/MH 18, Patient Journey 16, Ruff correctness gate and compileall all passed; two Chromium viewports remained accepted; no POC cache directory or 8911 listener remained. Evidence frozen in `poc/medical_monitoring_ai_native_r1/docs/R1_BACKGROUND_PROGRESS_SHELL_EVIDENCE.md`.
