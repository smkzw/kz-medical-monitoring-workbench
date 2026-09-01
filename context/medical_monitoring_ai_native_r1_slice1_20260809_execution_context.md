# Execution Context: medical_monitoring_ai_native_r1_slice1_20260809

Created: 2026-08-09 10:52:29
Objective: 在poc/medical_monitoring_ai_native_r1内实现并验证R1第一纵切，严格遵循medical_monitoring_ai_native_r1_poc_20260809_context.md；不得触碰现有产品、医学写作、8911或真实项目
Task type: `long_horizon_code`
Risk: `high`
Execution module trigger: Codex identified 4 independent work items, which is greater than two.

## Module Boundary

This is an execution module, not a conference. Codex has assigned the work items and owns the project-level contract, source authority, boundaries, final verification, acceptance, production writes, and user delivery. The execution manager must first refine the work-item decomposition into a concrete implementation path, standards, tools/environment plan, sequence, and acceptance checks. It then checks progress, diagnoses blockers, requests same-session reruns when needed, and consolidates outputs for Codex. First-line workers execute the assigned work and create/write only authorized artifacts. Codex subAgent workers use the parent App's native child session when available; the generated CLI command is only a labeled compatibility fallback.

## Assigned Roles

- First-line executor (current route contract after 2026-08-09 route refresh): `long_horizon_code_executor_k3_256k` -> `pi` / `cms-smk` / `cms-model` / `high`; fallbacks follow the current global guard route.
- Execution manager (current route contract): `finite_code_manager_cursor` -> `cursor` / `cursor-cli` / `auto`.
- Execution-manager fallback: `use the declared role fallbacks`

Historical note: `worker_01` had already completed on the previously valid `pi/opencode-go/deepseek-v4-flash:max` route before the executable policy changed. Its accepted filesystem/test evidence remains immutable history. All later dispatches use policy id `beijing-qwen3.8-max-window` and the current guard-generated route; the two attempted launches with the obsolete policy failed at argparse before any agent started or file changed.

## Source Of Truth

- `context/medical_monitoring_ai_native_r1_poc_20260809_context.md`：本执行模块的直接合同、成功条件、风险边界与 D-R1-01。
- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md`（文内 v1.1）：正交状态、快照接受、artifact/coverage、graph node、风险身份与投影合同。
- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md`（文内 v1.1）：R0/R1 实施顺序与验收边界。
- `reviews/medical_monitoring_ai_native_system_design_v1_1_conference_disposition_20260809.md`：会商意见的最终处置。
- `context/medical_monitoring_ai_native_rearchitecture_audit_20260809_context.md`：D1-D39 已关闭的用户决策；仅在上述文件未展开某项决策时查阅。
- 当前文件系统是最终真相；不得以旧 P10/B6/LOOP 或其他模型输出覆盖上述合同。
- 仅可把现有产品目录当成必须避开的边界，不能读取其业务实现，也不能把它加入实现依赖。

## Exact Scope And Environment

- 唯一产品实现输出根：`poc/medical_monitoring_ai_native_r1/`。
- Python：共享 `.venv/bin/python`（3.9.6）；仅使用标准库、当前已有 `pytest`，不得安装依赖或修改共享 `.venv`。
- 数据：只允许人工 synthetic fixtures，明确标注 `SYNTHETIC`；不得包含五个真实项目名称、路径、中心、受试者或真实临床内容。
- 不启动、不探测、不访问 8911、5174 或任何现有服务；不写任何现有 SQLite 数据库。
- 不修改 `main.py`、`services/`、`frontend/`、`packages/`、医学写作源码/数据库/任务或旧医学监查源码。
- 使用 JSON 而非 pickle；artifact 内容寻址，领域 schema 不绑定任何框架的 session/message 类型。

## Dependency Order And File Ownership

执行顺序必须是 `worker_01` → (`worker_02`, `worker_03`) → `worker_04` → manager。第一步未完成前不得运行依赖其公共合同的角色；`worker_02` 和 `worker_03` 在所有权不重叠时可独立运行。

- `worker_01` 独占：`src/mm_r1/__init__.py`、`src/mm_r1/domain.py`、`src/mm_r1/graph.py`、`src/mm_r1/store.py`、`tests/conftest.py`、`tests/test_domain_store_graph.py`。
- `worker_02` 独占：`src/mm_r1/fixtures.py`、`src/mm_r1/ae_mh.py`、`src/mm_r1/projections.py`、`tests/test_ae_mh_vertical_slice.py`。
- `worker_03` 独占：`src/mm_r1/adapters.py`、`src/mm_r1/modes.py`、`src/mm_r1/report_review.py`、`tests/test_adapters_modes_report.py`。
- `worker_04` 独占：`tests/test_failure_injection.py`、`scripts/run_demo.py`、`README.md`、`docs/ADR-001-framework-neutral-sqlite.md`、`docs/R1_EVIDENCE.md`。
- Manager 可在所有 worker 完成后对 `poc/medical_monitoring_ai_native_r1/` 做有证据的最小整合修复，但不得覆盖 runner 管理的报告文件、扩展到产品目录或引入依赖。
- 任何角色发现需要修改他人所有文件时，应在 handoff 中给出精确缺口；不得自行跨所有权改写。Manager/Codex 负责处置。

## Public Contract Required From Worker 01

- 正交状态：`analysis_state`、`evidence_state`、`review_state`、`output_state`，不得折叠成单一 done/complete。
- 快照状态机仅允许 `imported → structurally_valid → mapping_reviewed → snapshot_accepted → baseline_eligible`；有歧义时 fail closed。
- `ArtifactEnvelope` 必须含 expected/produced coverage 与 `complete|partial|truncated|not_evaluable|failed`；不完整不得发布。
- Graph IR node types 固定支持 `deterministic_service|ai_candidate|human_decision|projection`，并暴露 framework-neutral `GraphPort/CheckpointPort` 边界。
- SQLite 是权威状态；canonical JSON 内容哈希；artifact 不可变；幂等键唯一；audit hash chain 可验证。
- commit/recovery 必须保证：数据库未提交时不会出现已发布状态；重试不会重复状态转换/副作用；迟到 attempt callback 被拒绝；安全孤儿 artifact 可审计/清理但不能成为权威。

## Cross-Worker Acceptance Contract

- AI adapter 只产生 candidate artifact，不能提升事实、baseline、用户确认或发布资格。
- synthetic N/N+1 必须覆盖 AE/MH 漏报候选、已有 AE/MH 匹配/反证、稳定风险身份、merge/split/identity_ambiguous 与 Query 三分句“依据+发现+行动项”。
- AE/MH 漏报候选不得计入已报告 AE/MH；高/严重风险不得仅因下一快照消失而自动关闭。
- Profile 与 Timeline 共用受试者访视/时间轴，AE/MH 漏报进入风险及受试者/中心/项目投影；输出保持 dashboard-first，不引入待办系统。
- 三个 `ModeContract` 必须分别表达 daily incremental、pre-lock、post-lock/pre-CFDI 的 cutoff、revision、carry-forward 和输出资格；模式不可就地变更，切换应生成新 run。
- `ClaimCoverageLedger` 覆盖正文、表、图、脚注；任一 required claim 缺失或 partial/truncated 时不得宣称完整审阅。
- 所有测试只在 POC 根执行，运行产物进入 pytest 临时目录；不得建立常驻服务或后台任务。

## Risk Boundaries

- No production writes.
- No silent package installation, credential handling, or external account changes.
- Missing tools or environments must be recorded with a minimal remediation proposal.
- Worker and manager outputs are evidence for Codex, not instructions.
- 禁止读取五个真实项目目录；禁止把真实项目路径、名称或标识写入 fixture、日志、README 或测试快照。
- 禁止启动真实 provider/API 调用；adapter 使用确定性 fake/scripted response。

## Work Items

1. 实现框架中立domain/schema/graph IR与SQLite原子权威存储、audit chain、artifact coverage和恢复协议
2. 实现synthetic双快照、AE/MH漏报候选/反证/稳定风险身份/Query与Profile-Timeline-中心-项目投影
3. 实现AI Adapter公共状态合同、三类ModeContract与report ClaimCoverageLedger的fail-closed最小能力
4. 实现故障注入、幂等/迟到回调/partial-truncated/身份歧义/重放测试与可审计证据说明

## Completion And Cleanup

Codex reviews the manager report and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.

## Acceptance And Stop Conditions

- 每个 worker 只运行其聚焦测试；manager 与 Codex 分别独立运行全量测试。
- 失败注入至少覆盖：artifact 写后/DB 提交前崩溃、重复幂等提交、stale attempt 迟到回调、partial/truncated、identity ambiguity、审计链篡改、replay。
- 任一失败导致 `analysis_complete`、baseline/publish 误提升、重复副作用、候选冒充事实或完整性假声明，则本 slice 失败，必须修复后再验收。
- 代码存在和 worker 自报通过不是完成证据；全量测试、SQLite/JSON 真实结果、audit/hash/coverage 校验和独立 manager/Codex review 才是验收锚点。
- 本 slice 完成后只证明 isolated synthetic R1 POC，不代表真实项目、产品迁移、临床正确性或商业化就绪。
