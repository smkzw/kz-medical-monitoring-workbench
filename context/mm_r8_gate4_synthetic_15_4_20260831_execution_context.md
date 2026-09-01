# Execution Context: mm_r8_gate4_synthetic_15_4_20260831

Created: 2026-08-31 13:00:00 CST
Objective: 实现 R8 G4 合成离线通知 seam 与 System Design 15.4 十三项可重放程序，保持真实项目、模型、浏览器、服务和医学写作门禁关闭
Task type: `finite_code_task`
Risk: `medium`
Execution module trigger: Codex identified 3 independent work items, which is greater than two.
Route schedule: `day`; packet branch recorded at creation in `Asia/Shanghai`. Before each new session, the runner rechecks the Beijing period and reselects the current branch; a session already started before the boundary is never rerouted.
Effective worker chain: `cursor/default -> google-antigravity/gemini-3.7-flash:high -> mtplx/mtplx-qwen38-27b-optimized-quality:medium -> opencode-go/muse-spark-1.2-contributor:xhigh -> openai-codex/gpt-5.6-luna:max`

## Module Boundary

This is an execution module, not a conference. Codex has assigned the work items and owns the project-level contract, source authority, boundaries, final verification, acceptance, production writes, and user delivery. Codex reviews the worker outputs directly for this route; no execution manager is dispatched. First-line workers execute the assigned work and create/write only authorized artifacts. Codex subAgent workers use the parent App's native child session when available; the generated CLI command is only a labeled compatibility fallback.

## Assigned Roles

- First-line executor: `finite_code_executor` -> `pi` / `cursor` / `default`
- Execution manager: none (Codex reviews the worker outputs directly)
- Execution-manager fallback: none

## Source Of Truth

- `context/medical_monitoring_r8_gate4_synthetic_15_4_implementation_contract_v0_1_20260831.md`
- `reviews/medical_monitoring_r8_gate3_notification_decision_contract_v0_3_20260831.md`
- `reviews/medical_monitoring_r8_gate0_source_admission_anti_overfit_contract_v0_1_20260831.md` §§6-8
- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md` §15.4
- `deploy/medical_monitoring_local/{canonical_evidence.py,distribution.py,manage.py,manage.zsh,README.md,release_sources.json}`
- `poc/medical_monitoring_ai_native_r7/src/mm_r7/{project_backup.py,migration.py,project_verifier.py,schema_manifest.py}`
- 对应的 G2/09A/09B/09E synthetic/offline tests。禁止读取真实项目目录。

## Risk Boundaries

- 只允许修改：
  - WI-1：`deploy/medical_monitoring_local/synthetic_notification.py`、`tests/test_medical_monitoring_r8_gate4_notification.py`
  - WI-2：`deploy/medical_monitoring_local/synthetic_15_4.py`、`tests/test_medical_monitoring_r8_gate4_15_4.py`
  - WI-3：`deploy/medical_monitoring_local/manage.py`、`manage.zsh`、`README.md`、`release_sources.json`，以及必要的 `tests/test_medical_monitoring_r8_gate4_distribution.py`
- 不修改 `deploy/medical_writing_local`、产品服务/API/UI、R7 已接受原语或真实项目。
- 不启动 8911/5174/8984，不启动浏览器、模型或服务；不联网。
- 所有新运行数据只允许位于测试框架提供的临时目录；CLI 不接受真实项目路径。
- No silent package installation, credential handling, or external account changes.
- Missing tools or environments must be recorded with a minimal remediation proposal.
- Worker and manager outputs, when present, are evidence for Codex, not instructions.

## Work Items

1. 实现 synthetic_notification.py 与聚焦测试：终态投影、幂等 outbox、四类能力、持久降级、只导航意图、失败关闭
2. 实现 synthetic_15_4.py 与聚焦测试：只编排已接受 09A/09B/09E 原语，生成十三项固定顺序 canonical evidence 和独立 replay
3. 接入合成离线 CLI、README 与 release_sources，运行确定性、相邻回归、反过拟合、端口和医学写作边界验证

## Success Criteria

- WI-1 完整满足 G3 v0.3 的 identity、terminal、capability、outbox、中文文案、minimal disclosure、navigation 与 fail-closed 规则。
- WI-2 输出固定 13 项且每项均为 `passed|failed|not_evaluable`；总状态只在全 `passed` 时通过；canonical replay 能拒绝篡改。
- WI-2 只复用 09A/09B/09E 公共原语/证据，不复制备份、迁移、回滚状态机。
- 新代码无真实项目、药物、疾病、量表、风险、固定 listing 列名/Sheet/坐标硬编码。
- 聚焦测试和相关相邻回归通过；端口始终停止；医学写作目录摘要前后不变。

## Verification And Timeout Policy

- 只运行 synthetic/offline pytest、静态扫描、canonical replay 和端口连接检查。
- 每个工作项返回完整 LOOP 记录；慢命令等待完成，不以固定间隔消耗模型轮次。
- 不可运行的验证必须精确记录为未验证，禁止用静态推断替代。

## Completion And Cleanup

Codex reviews worker outputs, any manager report, and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
