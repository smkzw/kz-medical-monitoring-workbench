# Protocol 多 Agent 正式设计规格自审

日期：2026-08-09  
审阅对象：`plans/mw_protocol_multi_agent_rearchitecture_design_20260809.md`  
结论：`READY_FOR_FRESH_CONTEXT_CHALLENGE`，不是实施批准。

## 范围与边界

- 只审阅 Protocol 多 Agent 目标设计；未修改产品源码、schema、数据库或运行态。
- D017 为最新范围权威：Protocol 专属图；Standalone Synopsis 仅在 Protocol
  全链通过后导出；CSR 未来另建工作流。
- 当前暂停的 UI Goal 仍含 D017 之前的“独立双向 Synopsis”措辞，已视为
  superseded context，不作为本规格或会商权威。

## 已纠正的问题

1. **Synopsis 术语和循环门**：区分正文 `Protocol Summary` 与最终
   `Standalone Synopsis`；四层 Protocol 门不再依赖尚未允许生成的独立导出。
2. **Agent⑤缺失**：补齐统筹、版本、任务、产物、恢复和用户沟通合同，并
   明确其不得改事实、替代 Agent④或主观宣告完成。
3. **Skill 仅停留在概念**：增加版本化 SkillDefinition 和各 Agent 的 Skill
   组合；110 个 chapter-skill package 不等于 110 个常驻 Agent。
4. **资料门不完整**：在严格全量竞品 E1 外增加 E0 可复现发现、E2 当前
   法规/指南版本、E3 医学实质准入/章节覆盖；禁止零结果 `0=0` 和缩小分母。
5. **画布第二事实源风险**：明确 SemanticDocumentRevision 的文字/版式
   权威边界；手工/AI事实变更必须转 typed proposal 并传播影响。
6. **数据库选择过早固化**：PostgreSQL 保留为首选目标，但通过 repository
   抽象和 Phase 1 PoC 后才能锁为实施基线。
7. **Word 像素 hash 脆弱**：改为规范化 OOXML 结构指纹、原生操作回执与
   可容差视觉比较，不以逐页像素 hash 作为唯一条件。
8. **模板身份不充分**：写入 TP-MA-07 当前路径/hash；Ⅰ期真实模板未确定前
   不得冒充完成Ⅰ期合同验收。

## 确定性检查

- Markdown 共 792 行、81 个标题、2 个配对代码围栏；无相邻非空重复行。
- `TODO/TBD/待确认` 只出现在“最终产物禁止项/痕迹必须为0”的规则语境，
  未作为未决设计占位符。
- Protocol-only、CSR-out、Protocol Summary、Standalone Synopsis、Agent⑤、
  SkillDefinition、SemanticDocumentRevision 和 Gate E0–E3 均有显式合同。

## 必须由独立会商重点反证

- StudyDefinition 与 SemanticDocument 的双域权威是否仍可能产生事实漂移；
- E1 全量竞品门是否存在不可恢复死锁或通过 reclassification 被规避；
- 110 个章节合同是否足以覆盖 claim/evidence、跨章、Word 和适用性；
- LangGraph 重放与产品 event ledger 的事务边界、outbox 和迁移是否完整；
- PostgreSQL 本地运维成本是否真的优于继续强化 SQLite；
- 完整 Word 式 Web 编辑、原生 Word round-trip 和外部回流是否有可实现的
  开源技术路径；
- Agent④隔离、Harness 权限与敏感 checkpoint 是否足以 fail closed；
- 最终上线矩阵是否可证明“完整可提交正文”，而不是再次只验证流程可点。

## 自审判定

规格已足以交给 fresh-context verifier 做反证，但未达到实施 READY。必须先
完成正式会商、修订、用户书面复核和详细实施计划。
