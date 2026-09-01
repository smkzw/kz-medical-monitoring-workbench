# Task Context: medical_monitoring_r4_d10_artifact_20260816

Created: 2026-08-16 04:33:21
Objective: 依据冻结 D10 v0.6 合同构建并冻结 synthetic/offline 312+ case catalog、独立 oracle、registry、双生成器与 quota manifest；不实现 runtime/UI，不启动服务，不读取真实项目，不触碰医学写作。
Task type: `finite_code_task`
Risk: `high`
Selected agent route: `opencode-go` / `deepseek-v4-flash` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `reviews/medical_monitoring_r4_d10_project_signal_slice_contract_v0_6_20260816.md`，冻结 SHA-256 `c613bb7cad82caa6fa477ee2dd28bfca48b805b73503c646401a0aa237deff95`。
- `context/medical_monitoring_r4_d10_contract_acceptance_record_20260816.md`。
- `context/medical_monitoring_r4_d10_contract_pause_20260816.md`。
- D09 已纠偏并冻结的 artifact 模式，仅作工程结构参考：`tools/generate_d09_challenge_registry.py`、`tools/generate_d09_expected_oracle.py`、`tests/test_d09_artifact_generator.py` 及对应 D09 JSON 工件。
- 当前文件系统为最终事实；禁止以旧记录覆盖当前文件。

## Scope

- In scope：在本工作台内构建 D10 synthetic/offline artifact phase：不少于 312 例的 exact-key typed catalog、独立 oracle、五列双射 registry、catalog/registry generator、oracle generator、partition quota/mandatory-attack manifest、非 LLM 冻结测试。
- In scope：机器证明 12 个互斥 primary partition 配额总和 312、合同两组攻击清单去重后的 32 个 mandatory attack 至少各一例、case-to-attack 双向映射、canonical JSON/NFC/finite/hash、双遍字节一致、catalog expected 字段全为 null、oracle 独立、generator/runtime import closure。
- Allowed write paths：`tools/generate_d10_*.py`、`tools/verify_d10_artifacts.py`、`tests/test_d10_artifact_generator.py`、`reviews/medical_monitoring_r4_d10_*_v1_20260816.json`，以及本任务自己的 `context/`、`prompts/`、`runs/`、`reviews/`、`metrics/` 记录。
- Out of scope：D10 evaluator/projection/runtime、`src/mm_r4`、D09 及更早源码/工件、R5/UI、8911/任何服务、五个真实项目、真实患者数据、外部模型医学内容、医学写作子系统、系统安全设计与测试。

## Success Criteria

- 工件总例数不少于 312，12 个 primary partition 互斥并满足冻结配额，union/duplicate/missing/intersection 机械证明闭合。
- 合同两组攻击清单去重后的 32 个 mandatory attack 均满足至少 1 例，manifest 正反向映射一致。
- catalog、oracle、registry、quota、双生成器及测试具备固定 schema、内容寻址、独立生成/验证边界；不得依靠 case-id 跳表、自由文本或 catalog disposition 泄漏 oracle 结论。
- `python3 tools/generate_d10_challenge_registry.py --check`、`python3 tools/generate_d10_expected_oracle.py check` 和 D10 artifact focused tests 全部通过，且 8911 无监听。
- 独立 verifier 在全新或与 worker 隔离的上下文对固定 SHA 快照给出接受；在此之前不得启动 D10 runtime。

## Risk Boundaries

- 只能写上列 allowed paths；不得修改冻结 v0.6 合同。
- 不得读取真实项目路径或医学写作子系统。
- 不得启动 8911、浏览器、产品服务或长驻进程。
- 不得实现 runtime；artifact 独立冻结前 runtime 继续锁定。
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.
- A provider catalog/auth/transport preflight is diagnostic, not a live capability verdict: timeout, auth refresh failure, malformed output, or a stale/incomplete catalog must be recorded and followed by one real route attempt. Explicit user-selected routes are not blocked merely because the catalog does not list them; only a missing executable or native transport boundary may stop before that attempt.

## Loop Log

- 2026-08-16 04:33:21: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-16 04:36:00: 复核冻结合同 SHA、暂停边界与 8911 停止；进入仅 artifact 的有界实施。
- 2026-08-16 07:20:00: 首轮 artifact 结构与 312/32 配额通过，但独立 verifier 发现 16 个语义篡改可重签绕过；定向修订后 20 variants 已 fail-closed。
- 2026-08-16 07:45:00: 第二轮 verifier 发现测试 verifier 复用生产规则、嵌套对象可整体自洽重签、stable core/source 仍依赖 synthetic case index；状态保持 `REVISE_D10_ARTIFACTS`，冻结门与 runtime 继续锁定。
- 2026-08-16 08:35:00: 第三轮已拆出独立 verifier 与 fixture authority，88 项 D10/99 项 D09 通过；verifier 仍缺固定 raw SHA/pin 与少数 mode/visibility/R2/Query/source/ModelEvidence 跨工件重建门，状态继续 `REVISE_D10_ARTIFACTS`。
- 2026-08-16 10:10:00: 固定 raw SHA/全链重签门与 105 项 D10 测试已通过；最终 verifier 仍发现 origin 互斥、Query uncovered/排序、hidden subject-site pair、accepted source membership、ModelEvidence provenance 五个窄缺口。继续同会话做最后定向修订；runtime 仍锁定。
- 2026-08-17 19:12: 原 Pi session 两次恢复未完成实施，触发 no-progress fallback；Codex Luna/max worker 已写入五门候选但在用户暂停指令下被 interrupt。当前候选 SHA 见暂停记录，未运行完成性检查或 verifier 复验；状态 `PAUSED_R4_D10_FIVE_GATE_CANDIDATE_UNVERIFIED`。
- 2026-08-17 21:35: 从当前文件系统继续并闭合五门候选；D10 106、D09 99、四项 check、外部 verifier raw-SHA `uchg` 锚点与 8911 停止均通过。全新隔离 Luna/max reviewer 在同一审阅会话由 `REVISE` 转为 `ACCEPT_D10_ARTIFACTS`。artifact phase 已冻结，runtime-only 下一阶段解锁；权威记录为 `context/medical_monitoring_r4_d10_artifact_freeze_acceptance_record_20260817.md`。
