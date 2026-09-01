# R2 Batch B Codex 负向门：VETO 1

日期：2026-08-10

范围：worker_02 初始 Batch B 快照；不代表 R2-A 回退或 R2 总体结论。

## 结论

VETO。`338 passed` 只能证明现有正向测试自洽；Codex 实际复现 9 条同合同 fail-open，故 Batch C 继续冻结。

## 已复现缺口

1. `BaselineService.set_data_baseline(..., is_baseline_eligible=True)` 信任调用方布尔值；从未注册到 AcceptanceService 的快照可成为 DataBaseline，且 `acceptance_evidence_hash` 可为空、identity digest 可为任意非空字符串。
2. `RunManager.create_run(..., snapshot_accepted=True)` 同样信任调用方布尔值，默认值甚至为 True；任意 `fake-snap/fake-rev` 可进入 daily run。
3. `MODE_CONTRACTS` 是普通可变 dict，模块宣称的不可变合同可被运行时替换。
4. `DiffService` 不读取 SnapshotAcceptance/DataBaseline authority；两个未接受快照可直接执行 incremental diff。
5. `SnapshotDiff.diff_hash` 只绑定 entry ID 和简化 config ID，不绑定 entry/config 完整语义；同 snapshot ID、不同新值 2/3 产生相同 diff hash。
6. `RiskCandidate.from_signal` 接受任意 caller-supplied `candidate_id` 且不验证派生 ID；两个不同内容可使用同一 ID，registry 会静默覆盖。
7. 普通调用者可直接构造 `AdjudicationRecord(is_machine_adjudicated=False, user_confirmed=True)`，只放一个任意 candidate ID 即可被 `RiskLifecycle.establish` 当作人工确认并建立风险。
8. `RiskLifecycle.establish` 对 caller-supplied RiskIdentity 只核对 project，不核对 subject/domain；S01/AE candidate 可绑定 S99/CM identity。
9. `RiskLifecycle.transition(... CLOSED ...)` 无需 adjudication、接受快照 coverage 或用户确认；可直接自动关闭。

## 相邻必须覆盖

- merge/split 必须验证裁决属于同项目、绑定目标风险、支持该动作；merge 不得跨受试者；失败不能留下半完成新实例。
- mode change carry-forward 必须包含直接 prior run；MonitoringRun/DataBaseline/AdjudicationRecord 等权威对象不得靠公开直构绕过 service。
- diff record key 缺失/unknown 必须 fail closed；FieldChange 必须绑定 mapping provenance；partial date 至少覆盖 YYYY、YYYY-MM 和 UN/UNK；hash 必须绑定完整 entry/config 语义。
- 注册同 ID 不同内容不得覆盖；RiskInstance 应验证 identity subject/domain 和 transition chain 连续性。

## 处置

原 worker 同会话定向修复并补负向回归；Codex 再运行 Batch B、全量、独立攻击与稳定 SHA gate。R2-A ACCEPT 保持不可覆盖历史，Batch C 继续冻结。
