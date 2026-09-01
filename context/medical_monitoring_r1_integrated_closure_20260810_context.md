# Task Context: medical_monitoring_r1_integrated_closure_20260810

Created: 2026-08-10 03:08:54
Objective: 审计 R1 步骤1-13的集成完成度，并在隔离 synthetic POC 中补齐从冻结输入、manifest/controller、candidate/QC、受众投影到 AE/MH、Patient Journey 与 Query 草稿的一条可恢复端到端闭环；保护产品与医学写作子系统，不运行真实项目或8911
Task type: `long_horizon_code`
Risk: `high`
Selected agent route: `cms-smk` / `cms-model` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md`，尤其状态权威、候选与事实分离、共享受试者时间脊柱、后台进度与受众语言合同。
- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md` 的 R1 步骤 1-13、完成证据和当前恢复点。
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/**`、`tests/**`、`scripts/run_demo.py` 与 `docs/**` 的当前实现和已接受证据。
- `poc/medical_monitoring_ai_native_r1/slices/aemh_audience_workbench/**`、`slices/patient_journey/**`、`slices/background_progress_shell/**` 的只读数据合同和测试。
- 当前文件系统、临时目录中的 synthetic 运行结果和实际命令输出是最终事实。
- 2026-08-09 的框架/Patient Journey 外部调研与 ADR 已覆盖未变化的技术决策；本阶段只做集成收口，不重复仪式化搜索。若审计发现需要引入新框架、服务或依赖，必须重新开启发现门并停止实现。

## Scope

- In scope:
  - 逐项形成 R1 1-13 的证据矩阵，区分“单模块已证明”“同一运行已贯通”“仍缺证据”，不得把测试数量当成集成证据。
  - 在一个新建的隔离模块中编排一条同 Store、同 run、同 accepted N/N+1 snapshot、同 manifest revision 的 synthetic 闭环。
  - 复用现有 `CapabilityWorkUnitController` 与注入式 synthetic API transport 完成至少一个 AI-candidate work unit；原始输出先持久化、候选不晋升事实、无外部 endpoint/provider 调用。
  - 复用现有 AE/MH 纵切、coverage/QC、risk/query/projection 与 `SubjectTemporalSpine`，输出来自同一运行身份的风险驾驶舱、Profile、Timeline/Patient Journey 和三分句 Query 草稿。
  - 所有工作进度只落入现有 manifest work-unit ledger，并通过 `project_audience_progress` 读取；不建立第二套完成数或百分比。
  - 验证关闭并重开 Store 后可从权威中间工件继续，已经终态的 work unit 不重复副作用；故障窗口继续遵循已记录的 at-least-once＋稳定幂等键边界。
  - 提供 caller-supplied 新目录 CLI、聚焦测试、审计文档与 compact handoff。
- Work items / assignments:
  1. `WI-1 Evidence audit`：建立 R1 1-13 矩阵并列出真正断链，不改已接受模块来制造“全绿”。
  2. `WI-2 Integrated orchestrator`：实现同一权威 run 的最小编排和可恢复中间工件。
  3. `WI-3 Acceptance harness`：实现 CLI 与故障/重开/幂等/受众合同测试。
  4. `WI-4 Handoff`：报告当前通过项、未证明项和 Codex 必须亲自复核的目标。
- Out of scope:
  - 产品源码、医学写作子系统、8911、五个真实项目、真实 API/provider/harness、真实临床判断与任何外部写入。
  - 修改三个已接受 UI 切片、重新设计其视觉、引入 LangGraph/Temporal 或新依赖。
  - 把当前静态 Patient Journey 夹具伪称为由本集成运行生成；若尚不能共享同一运行身份，应在审计中明确，而不是复制 ID 掩盖断链。
  - R1 总体验收、R2 迁移、产品/商业/监管就绪声明。

## Success Criteria

- 形成可审计的 R1 步骤 1-13 状态矩阵，每一项有代码/测试/文档定位和明确结论。
- 新闭环的一次正常运行从 synthetic accepted snapshot 到 dashboard/Profile/Timeline/Query 全部共享 project/run/snapshot/temporal-spine/evidence identity；输出中不存在第二来源的静态身份拼接。
- manifest 分母包含实际闭环工作项；受众 `completed/total/percent` 与 ledger 逐项相等，且不暴露 provider/model/attempt/backend/hash/log 等内部信息。
- synthetic controller transport 只调用一次并保存 raw/candidate evidence；结果不会生成 canonical fact 或用户确认。
- coverage 不完整、控制器失败或中间 artifact 损坏时，后续 publication/output gate 失败关闭；不得仍输出“已完成”。
- 同一路径重放与 Store reopen 不重复已提交工件；冲突输入失败关闭。
- CLI 拒绝覆盖已有输出，所有输出只写调用者提供的新目录；无服务、无固定端口、无真实数据。
- 聚焦测试、R1 core、AE/MH 和 Patient Journey 相邻回归通过；独立 reviewer 决定本切片是否接受。

## Risk Boundaries

- Authorized writes are limited to new/updated isolated POC paths:
  - `poc/medical_monitoring_ai_native_r1/src/mm_r1/integrated_closure.py`
  - `poc/medical_monitoring_ai_native_r1/scripts/run_integrated_closure.py`
  - `poc/medical_monitoring_ai_native_r1/tests/test_integrated_closure.py`
  - `poc/medical_monitoring_ai_native_r1/docs/R1_INTEGRATED_CLOSURE_GAP_AUDIT.md`
  - a small README addition only if required to run the new CLI.
- Existing accepted source modules, tests, UI slice sources/data and evidence are read-only in the delegated round. If their contract blocks coherent integration, report the exact blocker rather than editing around it.
- No dependency install, no network call, no service, no browser and no fixed port in the delegated round. Codex owns any later browser acceptance.
- Fixture IDs and text must be fictional and synthetic; no copied real project or subject content.
- Do not write to product paths or the medical-writing subsystem.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.
- A provider catalog/auth/transport preflight is diagnostic, not a live capability verdict: timeout, auth refresh failure, or malformed probe output must be recorded and followed by one real route attempt. Only a missing executable or explicit invalid/retired/unlisted model may stop before that attempt.

## Loop Log

- 2026-08-10 03:08:54: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-10 03:14: Main venue re-anchored R1 steps 1-13 and current modules. Initial direct audit found the important integration gap: `run_demo.py`, AE/MH audience data, Patient Journey fixture, controller/progress shell are each proven but are not yet one same-run evidence chain. The bounded edit contract therefore targets a new orchestrator and leaves accepted modules read-only.
- 2026-08-10 03:20-03:50: one persistent Pi/cms-smk/cms-model execution session produced the bounded four-file implementation and completed two same-session corrective passes. Main-venue replay rejected the first overclaims, then corrected completed re-entry, both Store close/reopen interruption points, public controller/runtime skip handling, truthful partial evidence, 7-unit progress, and actual raw/candidate integrity gating.
- 2026-08-10 03:58: focused closure suite `41 passed`; full isolated R1 suite `326 passed`; AE/MH audience suite `18 passed`; Patient Journey suite `16 passed`; Ruff `E9,F63,F7,F82` and isolated `compileall` passed. A real caller-supplied temporary CLI directory produced `draft_exportable`, evidence `complete`, progress `7/7`, one synthetic transport, recovery JSON, and rejected a second write to the now non-empty directory.
- 2026-08-10 04:00-04:14: native Luna capability probe was rejected as unavailable, so the declared Codex CLI compatibility route used `gpt-5.6-luna` at max in read-only mode. The fresh reviewer verified the frozen four-file hashes twice and independently reproduced identity, zero-side-effect re-entry, both interruption continuations, failure/skip terminal states, raw/candidate tamper QC blocking, candidate/fact isolation, shared temporal spine, three-part Query and 7/7 audience progress. Verdict: `ACCEPT`, no P0-P4 implementation findings. Its file-backed pytest was blocked by the review sandbox, so Codex's file-backed test evidence remains the deterministic anchor.
- 2026-08-10 04:15: integrated-closure slice accepted. This acceptance does not close R1 overall; static audience/runtime connection, OS-level crash durability, real providers/projects, cross-process concurrency and product service remain outside this slice.
