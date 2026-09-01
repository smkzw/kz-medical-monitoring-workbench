# R2 Batch B Codex 负向门：VETO 2

日期：2026-08-10

范围：worker_02 follow-up 01 完成快照；不回退 R2-A ACCEPT，也不代表 R2 总体结论。

## 结论

VETO。runner 正常完成 2 个恢复轮次并自报 `323 passed`，但 Codex 源码审查与纯合成内存攻击复现 15 条 fail-open。Batch C 继续冻结。

## 已执行复现

以下结果均为成功绕过，而不是预期的 fail-closed：

1. `BaselineService._verified_baseline(...)` 可被普通调用者直接调用并制造 `snapshot_id='fake'` 的权威外观基线。
2. `RunManager._verified_run(...)` 可直接制造 `snapshot_id='fake-snap'` 的权威外观 run。
3. `RiskLifecycle._verified_instance(...)` 可直接制造无注册候选/裁决且 identity domain 不一致的风险实例。
4. 已接受 snapshot ID 可被另一份不同内容的 `ListingSnapshot` 替换后晋升 DataBaseline。
5. 任意 duck-typed 假 `AcceptanceService` 可晋升 DataBaseline。
6. 任意假 `AcceptanceService` 可创建 run，且接受假 snapshot/revision。
7. 对真实已接受 snapshot，RunManager 接受与绑定不一致的 `source_revision_id='evil-rev'`。
8. acceptance record 处于 `snapshot_accepted` 但 `blocked=True` 时仍可创建 run。
9. DiffService 接受同 snapshot ID 的不同内容替换，并计算为正式 diff。
10. DiffService 接受任意 duck-typed 假 `AcceptanceService`。
11. `issue_user_adjudication(..., user='attacker')` 产生 `user_confirmed=True`。
12. 只含无关 `source_revision_id='foreign-only'`、不绑定 candidate 的证据仍可签发裁决并建立风险。
13. `coverage_snapshot_id='fake', coverage_snapshot_accepted=True` 可直接关闭风险；仍信任调用方布尔值。
14. 人工确认 escalation 后 `confirmed_by_user` 未沿生命周期保留，随后机器裁决可关闭该风险。
15. merge 裁决只绑定第一个风险仍可合并第二个未绑定风险；split 可把一个受试者风险拆到 S02/S03。

## 源码相邻缺口

- Baseline/Run/Diff 未要求真实 `AcceptanceService` 类型，也未比对 service 中的 `SnapshotBinding.snapshot/source/content`；Diff incremental 也未由 BaselineService 验证 DataBaseline 注册身份。
- Run/Diff 忽略 `rec.blocked`；Run 的 revision/mapping/identity 仍由调用方字符串提供，而不是从绑定派生。
- Diff 的 `canonical_field_map` / `mapping_ids` 仍由调用方提供；空 `record_key_fields` 可在单行时通过；映射 provenance 未绑定接受快照的真实 MappingDefinition。
- 风险 actor 只要求非空；AdjudicationRecord 未绑定 action 与完整 targets；merge/split 未验证目标集合及原状态，RiskInstance 未验证 domain/transition 连续性。
- 用户确认只在建立时写入，后续人工裁决不形成不可丢失历史标志。
- 初版 worker 报告为 102 个 B 测试（35/18/21/28），follow-up 01 变为 87（33/13/21/20），净少 15；不得以删除、替换或弱化旧测试取得通过。

## 处置

原 worker 同会话执行第二次、最后一次定向修复：恢复初版 102 项行为覆盖，叠加本 VETO 全部负向回归；使用真实 service/binding/target/action authority，移除所有普通调用者可达签发器与授权布尔值。Codex 再运行独立攻击、B/全 R2、编译、隔离和稳定 SHA 门。R2-A ACCEPT 保持不可覆盖历史，Batch C 继续冻结。
