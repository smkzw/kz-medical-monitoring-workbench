# R2 领域内核、审计与迁移底座实施合同

日期：2026-08-10

## 目标与冻结边界

在 `poc/medical_monitoring_ai_native_r2/` 建立可删除、synthetic/offline 的独立实现，完成 R2 步骤 1–11。R1 是只读迁移基线；产品、医学写作、真实项目、8911、共享运行库和真实 provider/harness 保持冻结。SQLite 继续是唯一领域权威，框架 checkpoint 不能替代领域对象、进度或发布状态。

## 批次 A：schema、来源与事实资格

- 建立单一 schema registry、版本/兼容性/升级合同。
- 实现项目、不可变来源、全量 listing 快照、内容寻址 artifact。
- 实现 KnowledgePack、RuleActivation、Mapping、CanonicalFact 版本合同。
- 实现 SnapshotAcceptance、source coverage、record identity 与 baseline eligibility 状态链。
- 验证：单元/属性测试、非法跳级、未知 schema、hash/identity 冲突、并发相同导入和失败注入。

## 批次 B：风险、裁决、双基线与模式

- 实现 RiskCandidate、RiskInstance、RiskTransition、AdjudicationRecord。
- 冻结稳定风险身份，以及 merge/split/identity_ambiguous/superseded/not_evaluable。
- 分离数据基线与医学决定版本。
- 实现 daily/pre_lock/post_lock_pre_cfdi ModeContract 与 full/incremental 快照 diff。
- 验证：生命周期追加性、歧义阻断、模式不可静默转换、消失记录/范围变化、规则/知识变化不伪装数据变化。

## 批次 C：审计、原子提交与迁移

- 实现项目级 tamper-evident 业务审计和验证工具，技术日志分离。
- 实现 checkpoint、artifact/state/audit 原子提交、幂等 side-effect gate、publication gate。
- 实现 R1 只读 adapter、合成双读差异、schema 迁移/回滚/恢复演练。
- 验证：改写/删除/插入检测、重复/迟到/中断/损坏/并发、事务失败点、旧资产零写入、回滚后身份与审计一致。

## 分工和完成权

- 实施 worker：只在 R2 namespace 和本任务记录表面工作；按批次提交路径、测试与残余风险。
- Codex：逐批读取实际 diff/文件，运行决定性测试、检查越界与 8911，必要时做小范围修复。
- 独立 reviewer：fresh context，只获得 artifact、验收标准和非 LLM 锚点；可 ACCEPT/VETO，不可静默改写。
- R2 只有在三批完成、全套测试与迁移/篡改证据通过、独立 reviewer 接受、Codex review gate 通过后才完成。
