# Codex Execution Review: mm_r7_slice09b_contract_20260830

## Verdict

`READY_FOR_INDEPENDENT_CONTRACT_CONFERENCE`

三项只读执行工作已形成互补证据：逐库版本/结构清点、升级与恢复状态机、面向中文医学监察员的兼容与进度契约。Codex 已将其合并为 `medical_monitoring_r7_slice09b_schema_migration_contract_v0_1_20260830.md`，但合同在独立会商前仍为提案状态。

## Boundary Compliance

- 未修改 R1/R7 产品源码、前端或医学写作子系统。
- 未启动 8911/5174、浏览器、模型、provider 或真实项目。
- 仅使用源码读取和系统临时目录中的 synthetic SQLite 探针。
- 三个 worker 均使用声明的 `pi/openai-codex/gpt-5.6-luna:max`，无 fallback 或模型替换。
- guard/runner 生成并执行 Hermes-compatible 治理包；Hermes 未作为 Pi/OpenAI-Codex 的传输层。

## Worker Findings Accepted Into Contract

1. R1 constructor 会把未知 marker 覆盖为 `6`，profile/binding 可打开结构损坏表；09B 因此必须在任何普通 constructor 前进行独立只读识别。
2. launch registry 是当前唯一具备事务化、marker-last、故障回滚的成熟迁移面，可保留其 DDL/backfill 语义，但必须转入 staging-only 显式 runner。
3. v0.1 目标限定为当前 accepted set：R1 `6`、launch v4、profile/binding/risk 当前 v1 结构；不创造下一版本。
4. R1 marker `3` 因与 09A 恢复点支持集合冲突而暂不纳入；v0.1 只允许 `4/5→6`。
5. 项目打开不自动升级；受支持旧格式完整可读时保持后端强制只读，用户明确点击后才升级。
6. 医学写作完全排除在 09B DTO、迁移和写阻断测试范围之外，只验证其路径未变化。

## Codex Adjustments

- 拒绝“缺失非关键字段仍有限展示”的建议：医学监察员容易把局部页面误认为全量记录，v0.1 只允许完整可读或阻断。
- 不在医学监查 DTO 中暴露 `medicalWritingMode`；跨子系统状态不是本切片职责。
- 进度采用实际证据里程碑，不能用耗时、行数或文件大小估算。
- 明确 operations ledger 在项目目录切换之外，并新增 migration plan/checkpoint，而不是把 09A restore 伪装成迁移器。

## Remaining Gate

对 v0.1 合同执行独立 conference。任何 P0–P4 发现均需在同一 session 中补充审阅；只有合同会商归零后才允许实现 09B 产品源码。

## Cleanup Decision

合同会商和冻结记录完成前，不归档本 execution packet。
