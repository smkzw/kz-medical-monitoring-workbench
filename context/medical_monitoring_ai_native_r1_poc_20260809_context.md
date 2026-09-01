# Task Context: medical_monitoring_ai_native_r1_poc_20260809

Created: 2026-08-09 10:50:16
Objective: 按已批准System Design v1.1与R0-R8计划，在全新隔离目录完成R1非真实POC：验证状态权威、快照接受、artifact coverage、恢复原子性、AI adapter公共合同、synthetic双快照、AE/MH纵切、三模式和报告claim coverage；保护医学写作子系统，不启动8911，不读取五个真实项目
Task type: `long_horizon_code`
Risk: `high`
Selected agent route: `opencode-go` / `deepseek-v4-flash` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md`（文内 v1.1）。
- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md`（文内 v1.1，尤其 R0/R1）。
- `reviews/medical_monitoring_ai_native_system_design_v1_1_conference_disposition_20260809.md`。
- `context/medical_monitoring_ai_native_rearchitecture_audit_20260809_context.md` 中 D1-D39 与会商恢复检查点。
- 当前文件系统；现有医学监查/医学写作产品源仅用于边界识别，本 R1 不读取其业务实现、不修改其文件。
- 官方实现候选证据：LangGraph persistence/docs 与 MIT repo；Microsoft Agent Framework workflow/checkpoint docs 与 MIT Python package；Temporal Python SDK MIT repo；SQLite transaction/atomic commit docs；Python `sqlite3` docs。

## Scope

- In scope: 新建并仅修改 `poc/medical_monitoring_ai_native_r1/`；建立框架中立 Graph IR、SQLite 权威存储、正交状态、快照接受、artifact/coverage、原子提交/恢复、adapter contract、synthetic 双快照、AE/MH 漏报纵切、三级/Subject 投影、三模式最小合同、report claim coverage 和故障注入测试。
- In scope task records: 本 context、`reviews/codex_medical_monitoring_ai_native_r1_poc_20260809_review.md`、`metrics/medical_monitoring_ai_native_r1_poc_20260809_metrics.md` 及 guard-owned run/prompt files。
- Out of scope: `main.py`、`services/`、`frontend/`、`packages/`、医学写作数据库/运行时/任务、8911/5174、旧 P10/B6/LOOP、任何真实项目目录或真实临床内容、产品迁移、外部模型真实调用。
- Out of scope: 安装或承诺 LangGraph、Agent Framework、Temporal；R1 先证明领域与恢复不变量，再做独立框架 spike。

## Success Criteria

- 新目录无真实项目路径或项目名硬编码，synthetic fixtures 明确标识非真实。
- SnapshotAcceptance 严格按 imported → structurally_valid → mapping_reviewed → snapshot_accepted → baseline_eligible；歧义阻断 baseline。
- ArtifactEnvelope 区分 complete/partial/truncated/not_evaluable/failed，并对 expected/produced coverage 做确定性对账；不足不得发布。
- Node/Run/Artifact/Audit 通过单事务与内容哈希保持可恢复；重复提交、迟到回调、崩溃注入不产生假通过或重复副作用。
- Adapter contract 能表达正常、失败、超时、取消、partial/truncated 与独立 binding，不需要真实 provider。
- synthetic N/N+1 能产生 AE/MH 候选、反证/匹配、风险稳定身份、三段式 Query、Profile/Timeline/中心/项目投影；候选不得计入已报告 AE/MH。
- 三个 ModeContract 对 cutoff、revision、carry-forward 和输出资格 fail closed。
- report fixture 覆盖正文/表/图/脚注并维护 ClaimCoverageLedger；遗漏时不宣称完整审阅。
- 所有新增测试通过；独立 reviewer 审阅通过或所有意见已处置；Codex 复核文件、测试和恢复证据。

## Risk Boundaries

- 允许写入路径仅为 `poc/medical_monitoring_ai_native_r1/` 与本任务 guard/context/review/metrics/run 文件；其他产品与写作子系统路径只读或不触碰。
- 不启动/探测 8911、5174 或任何产品服务；不写现有 SQLite 数据库。
- 不读取、复制、扫描或运行五个真实项目；fixtures 必须人工构造且无真实受试者/中心/项目标识。
- 不安装新依赖，不修改共享 `.venv`、package lock、环境变量或凭据。
- 不删除历史过程文件；阶段性清理只处理本任务新建且已证明可再生的临时/缓存产物。
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Implementation Decision D-R1-01

- 选择：POC 第一纵切使用 Python 3.9 标准库 + SQLite 3.51 + JSON 内容寻址 artifact files，graph IR 保持框架中立。
- 原因：现有共享 venv 是 Python 3.9.6；当前 LangGraph 与 Microsoft Agent Framework 路线要求 Python 3.10+，Temporal 需要额外 server/worker。直接引入任一候选会先验证框架配置而非领域/恢复不变量，并增加对医学写作环境的影响面。
- 外部证据：SQLite 显式事务与原子提交适合单机最小权威；LangGraph、Agent Framework 和 Temporal 均提供 checkpoint/replay，但各有自己的 superstep/runtime/服务语义。
- 后续：R1 内核通过后，以同一 GraphPort/CheckpointPort 合同分别做候选 adapter spike；不得让 POC schema 绑定框架 session/message。
- 回滚：整个 `poc/medical_monitoring_ai_native_r1/` 可独立移除；不修改现有产品数据库或入口。

## LOOP Contract

- Objective: 证明一个可恢复、coverage fail-closed、候选与事实分离的 synthetic AE/MH 纵切。
- Hypothesis: 框架中立 IR + SQLite 单事务权威足以先验证核心不变量，并能暴露真正需要外部 orchestration framework 的缺口。
- Action: 先实现 schema/store/state machine，再添加 fixtures/domain nodes/projections，最后注入失败并重放。
- Observation: tests、SQLite rows、artifact hashes、coverage ledger、audit chain 和投影 JSON。
- Evaluation: 任一 partial/truncated/identity ambiguity/崩溃造成 `analysis_complete` 或重复副作用即失败。
- Decision: 通过后进入框架 spike；失败则缩小事务边界或修订状态合同，不扩大到真实项目。
- Record: 每个阶段只记录决定性命令、结果、失败假设和下一步。

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-09 10:50:16: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-09 10:50-11:00: v1.1、最新 AGENTS 与技能重新锚定；确认 workbench 非 Git 仓库，因此隔离新目录是保护用户并行修改的主要手段。
- 2026-08-09 11:00: 官方二次核验与本地环境检查完成；选择 D-R1-01，不安装框架/依赖，不触碰共享运行面。
- 2026-08-09: R1 slice1 execution contract 已补齐源权威、文件所有权、依赖顺序和 fail-closed 验收；五份角色提示执行 guard preflight。
- 2026-08-09: `worker_01` 主路由完成公共 domain/Graph IR/SQLite store，Codex 独立复核发现 coverage 发布门、快照身份折叠、冻结 graph 恢复、回调副作用等九组缺口，未予放行。
- 2026-08-09: 同一 session `019fe474-6cdf-7000-83e6-3a650b2a3aab` 完成纠偏；公共内核聚焦测试 `55 passed`，Codex 再跑关键缺陷过滤集 `7 passed, 48 deselected`。当前公共内核可供 worker_02/03 消费；仍未进入产品、真实项目或服务运行。
- 2026-08-09: worker_02/03/04 与 Cursor manager 完成纵切、故障注入和两轮权威边界纠偏。Pi 路由健康检查在 worker_02-04 建立会话前失败，按全局合同使用 Luna CLI compatibility；所有 session/route/fallback 原因已记入 execution metrics。
- 2026-08-09: Codex 拒绝 manager 初次接受的可伪造 `SnapshotBaselineProof` 残余，并封闭 direct `update_run_state(...EXPORTED)` 竞争路径；随后新增跨项目 eligible snapshot 与同项目错误 snapshot version 的 fail-closed 绑定。
- 2026-08-09: Codex 独立全量回归 `103 passed in 0.62s`。全新 synthetic demo 实际生成 SQLite/JSON：manifest `3/3`、Run `complete/complete/not_required/draft_exportable`、2 个权威 artifact、3 个 facts、28 个 domain objects、58 条可验证 audit event，恢复无 orphan/incomplete/integrity violation；candidate/fact 分离和 Profile/Timeline 共享 temporal spine 已核验。
- 2026-08-09: R1 slice1 判定为 isolated synthetic PASS；不代表 R1 整体、产品、UI、真实项目、provider、临床/监管或商业就绪。下一安全动作是归档本 execution packet，并在隔离 Python >=3.10 环境开展 R1 slice2 框架 adapter/work-event/restart spike。
- 2026-08-09: `review-gate --require-verification` 通过；guard 已把 slice1 prompts/runs/logs 归档到 `archives/execution/medical_monitoring_ai_native_r1_slice1_20260809/`。fresh demo 临时目录经精确核对后可恢复地移入废纸篓；POC 内无 `__pycache__`、`.pytest_cache`、`.pyc` 或 `.DS_Store`。
