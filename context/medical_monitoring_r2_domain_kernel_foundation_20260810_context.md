# Task Context: medical_monitoring_r2_domain_kernel_foundation_20260810

Created: 2026-08-10 05:15:41
Objective: 在独立 namespace 内实施 R2 领域内核、审计与迁移底座：建立单一 schema registry、StudyProject/SourceRevision/ListingSnapshot/KnowledgePack/RuleActivation/Mapping/Facts/Risk/Adjudication/ModeContract 权威，原子 artifact-state-audit 提交、checkpoint/idempotency/publication gate，以及旧资产只读 adapter 和合成双读差异；不触碰产品、医学写作、真实项目或8911
Task type: `long_horizon_code`
Risk: `high`
Selected agent route: `cms-smk` / `cms-model` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md`：已批准的领域对象、双基线、三模式、原子提交、审计、迁移和产品边界。
- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md`：R2 步骤 1–11 与完成证据。
- `poc/medical_monitoring_ai_native_r1/docs/R1_OVERALL_ACCEPTANCE_MATRIX.md` 与 `reviews/codex_conference_medical_monitoring_r1_overall_acceptance_20260810_review.md`：R1 已接受的 synthetic/offline POC 能力、限制和冻结基线。
- `poc/medical_monitoring_ai_native_r1/docs/ADR-001-framework-neutral-sqlite.md`：SQLite 单一领域权威、内容寻址 artifact 与 GraphPort 边界。
- `poc/medical_monitoring_ai_native_r1/docs/ADR-002-provisional-langgraph-orchestration-adapter.md`：LangGraph 仅为可替换控制适配器，不能成为领域、医学或进度权威。
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/` 与 `poc/medical_monitoring_ai_native_r1/tests/`：只读迁移基线和相邻合同证据。
- 当前文件系统为最终真相；历史记录只用于定位，不覆盖当前文件。

本轮不重新开启框架/存储选型：上述 ADR 已覆盖未变化的假设，R2 不新增运行框架或第三方依赖。若实现过程中出现必须新增依赖、第二控制平面或非 SQLite 权威的需求，先停止该分支并重新执行外部发现与 ADR。

## Scope

- In scope：在 `poc/medical_monitoring_ai_native_r2/` 建立独立 Python namespace 和可删除的 synthetic/offline R2 POC；单一 schema registry 与兼容性检查；StudyProject/SourceRevision/ListingSnapshot/KnowledgePack/RuleActivation/Mapping/Facts/SnapshotAcceptance；稳定记录与风险身份；RiskCandidate/RiskInstance/RiskTransition/AdjudicationRecord；双基线、三类 ModeContract、full/incremental diff；项目级 tamper-evident 业务审计；checkpoint、幂等副作用门、原子 artifact/state/audit 提交与 publication gate；R1 只读 adapter、合成双读差异、迁移/回滚演练；单元、属性、迁移、并发、失败注入测试和独立 QC。
- In scope：只允许在 `poc/medical_monitoring_ai_native_r2/`、本任务 `context/`、`plans/`、`prompts/`、`runs/`、`reviews/`、`metrics/` 中写入与本任务直接相关的文件。
- Out of scope：产品源码、共享运行库、医学写作子系统、现有 R1 文件的功能性修改、真实项目或真实数据、真实 provider/harness、8911、产品数据库/入口、外部发布、旧数据库删除或真实迁移。
- Out of scope：R3 的异构 listing 智能识别、R4 的多风险域医学分析、R5–R8 的产品界面/全流程/真实项目验收；R2 只提供这些阶段所需的权威合同和迁移底座。

## Success Criteria

1. 单一、可查询的 schema registry 冻结所有 R2 领域对象版本，并对已知/未知版本、向后读取与不兼容写入 fail-closed。
2. 来源、知识、规则、mapping、事实、快照接受与 baseline eligibility 形成不可跳级、可审计的版本状态链；每次输入仍是全量 ListingSnapshot。
3. 记录和风险身份覆盖稳定、合并、拆分、歧义、取代、不可评价；风险生命周期追加，不覆盖历史；裁决与候选/风险身份绑定。
4. 数据基线与医学决定版本分离；daily/pre_lock/post_lock_pre_cfdi 三类 ModeContract 不可静默转换；full/incremental diff 能区分新增、修改、消失、范围变化及影响传播输入。
5. artifact 先不可变落盘并校验，随后在同一 SQLite 事务提交 state/audit 引用，最后推进 publication pointer；重复、迟到、中断、损坏和并发写入均有确定性结果。
6. 项目级业务审计链可重建并检测改写、删除、插入；技术日志与业务审计不混用。
7. R1 仅通过只读 adapter 接入；合成双读差异报告能证明或明确拒绝来源、事实、风险身份映射，不写回 R1。
8. 提供 schema 迁移、回滚、备份/恢复的隔离演练；明确冻结表和删除禁区；不触碰任何真实状态。
9. 相关单元、属性、迁移、并发和失败注入测试通过；完整测试不依赖网络、凭据、真实项目或 8911。
10. 独立 reviewer 依据实际文件、测试日志与迁移/篡改证据接受；Codex 复核后才可把 R2 标为完成。

## Risk Boundaries

- 这是 high-risk Tracked 隔离实现，不是产品批准。产品、医学写作、真实项目、8911、共享依赖与 R1 功能文件保持冻结。
- R2 只能建立新的隔离 namespace；不得复制凭据、真实项目路径、真实受试者数据或未脱敏日志。
- SQLite 是唯一领域、医学、Run 和发布权威；编排框架 checkpoint/session/message 只可保存可重建控制状态。
- LLM/Agent 只能提交候选 artifact；不得直接提升 canonical fact、snapshot acceptance、baseline eligibility、risk instance、adjudication 或 user confirmation。
- 旧资产 adapter 默认只读；迁移演练使用合成副本；当前阶段禁止删除旧表、旧数据库或 R1 artifacts。
- 所有 side effect 必须有幂等键和 publication gate；失败、中断、partial、truncated、not_evaluable 不能冒充成功或可发布。
- 不安装或升级共享依赖；如必须引入第三方包，只能先提出版本、许可证、安全、回滚与隔离验证方案，由 Codex 重新决策。
- 委派 worker 不拥有完成权；须提交变更路径、测试、失败路径、残余风险。独立 reviewer 只接受或否决，不静默改写。

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.
- A provider catalog/auth/transport preflight is diagnostic, not a live capability verdict: timeout, auth refresh failure, or malformed probe output must be recorded and followed by one real route attempt. Only a missing executable or explicit invalid/retired/unlisted model may stop before that attempt.

## Loop Log

- 2026-08-10 05:15:41: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-10: Codex 重新锚定 System Design v1.1、R0–R8 plan、R1 总体验收矩阵与 ADR；确认 R2 沿用 SQLite 单一权威/框架中立路线，不新增外部依赖，产品、医学写作、真实项目和 8911 继续冻结。
- 2026-08-10: R2 合同拆为三个顺序实施批次：A schema/source/knowledge/mapping/snapshot；B risk/adjudication/baseline/mode/diff；C audit/atomicity/idempotency/publication/migration/read-adapter。每批由 Codex 运行决定性测试并复核后才进入下一批；最终另做 fresh-context 独立验收。
- 2026-08-10: Batch A、Batch B 已分别取得独立 ACCEPT。Batch B 冻结快照 `ecf9d07df74fc3ff6a2d775a91683de24a6db2eecf77e6a6ad3f4f9ec02e064f`，全 R2 `493 passed`，无 cache，8911 无监听。用户最新约束是不再设计或测试额外系统安全能力；Batch C 仅保留用户功能必需的 SQLite 持久化、原子保存/恢复、发布读取一致性、R1 只读兼容和合成迁移/回滚，不开展攻防/安全专项，随后转入面向用户的 Patient Journey 与看板。
- 2026-08-10: Batch C 经过 Codex 修正、Luna 三轮 VETO 与 fresh-context Pi/CMS fallback 独立 ACCEPT 后完成。冻结 R2 清单 `69033e28616ca497579d7b3b9bbbd87ab8fc3031eb7d0259ba3954db1a338003`；R2-C `105 passed`、全 R2 `598 passed`、33 个 Python 文件编译；R1 `ba6692f...23d87` 未变，8911 停止。R2 阶段完成，下一步进入 R3，仍不触碰产品、医学写作或真实项目。
