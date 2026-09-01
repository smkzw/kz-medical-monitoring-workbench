# R2 Batch B 独立 VETO 纠偏门

日期：2026-08-10

状态：`REMEDIATED / PENDING_INDEPENDENT_FOLLOWUP`

来源：`runs/medical_monitoring_r2_batch_b_independent_review_20260810.md` 的 5 个 P1、1 个 P2。首次 VETO 报告与此前本地门均保留，不覆盖历史。

## 逐项纠偏

1. **旧裁决重放**：`AdjudicationRecord.target_risk_versions` 绑定每个目标的 `(risk_identity_id, risk_instance_id, last_transition_hash)`；使用时按当前实例复核，状态变化后旧裁决失效。
2. **错误 coverage 关闭**：风险建立必须传入并绑定来源 AcceptanceService；RiskInstance 保存来源快照集合。关闭必须使用同一服务、不同于来源且注册时间更晚的 baseline-eligible 全量快照；裁决证据必须绑定 coverage snapshot；机器关闭必须是 `rejected_by_evidence`。
3. **SAE/AESI 自动关闭**：保留规范化 `clinical_risk_flags`，从 severity 与候选 signal type 提取 SAE/AESI；高风险、SAE/AESI 或任何既往人工确认均禁止机器关闭。
4. **merge/split 人工确认丢失**：新风险继承所有祖先的 `confirmed_by_user`、来源快照与临床风险标记；原风险继续保留完整历史。
5. **调用方锁库布尔值**：删除 `user_selected_locked_version` 参数。`RunManager.select_locked_version(...)` 只为 AcceptanceService 配置的本地用户签发不可直接构造的 `LockedVersionSelection`；post-lock Run 必须绑定同一 RunManager 登记且与 live snapshot/evidence 一致的 selection ID。
6. **diff 嵌套顺序不稳定**：DiffEntry 对精确 FieldChange 记录按完整语义 payload hash 排序，并规范化 impact domains；反向输入产生相同 entry hash。

## 新增负向证据

- 裁决经过 escalate→deescalate 后重放旧 escalate：拒绝。
- 无关 AcceptanceService coverage 与复用来源 snapshot：拒绝。
- severity=`aesi` 及 signal type 含 AESI 且 severity=medium 的机器关闭：拒绝。
- 机器 merge/split 后新风险保留祖先人工确认，后续机器关闭：拒绝。
- 旧 `user_selected_locked_version=True` 调用：TypeError；跨 RunManager selection：拒绝。
- FieldChange 反向顺序：规范化后 entry hash 相同。

## 决定性检查

- Batch B：`184 passed in 0.19s`。
- R2 全量：`420 passed in 0.32s`。
- 原 VETO 重放脚本：8/8 `PASS`，`veto_replay_gate=PASS`。
- 内存语法编译：21 个 Python 文件。
- R2 cache directory：0。
- TCP 8911 listener：无。

## 冻结锚点

树哈希命令与独立审阅者一致：

```bash
find poc/medical_monitoring_ai_native_r2 -type f -print0 | sort -z | xargs -0 shasum -a 256 | shasum -a 256
```

- R2 tree：`5fbb2c79065869f340eba2f103b712bab95f16ce14f6b4b4942fd466c848c787`
- README：`56e5e2178f63d074af1cfaeaa89e773565d1152daa62d7f0d803906017b9d5a5`
- `src/mm_r2/__init__.py`：`67907ffd3640d5757cf9edacb27e0e9fff4a9455f3f949a2822fb8776734980a`
- `src/mm_r2/baselines.py`：`6a489e7e40004382c5684e7e005e6715e263da25611500cfd2e4f7d3f7b089fd`
- `src/mm_r2/modes.py`：`05a032b7fd42b0c0a8aaa150048d1531a685171eba5787efe14175100582d6ea`
- `src/mm_r2/diff.py`：`a4991ec9c17b7283e8978e7b5ebe6abf99be62ed8523d595ee448a208a17f91e`
- `src/mm_r2/risk.py`：`2251d7a45652242dfe8e75d636643581e333d201b2e76d082a569b72e6febd59`
- `tests/test_r2_b_baselines.py`：`c0b1047e143f432f0f388508a2aba5f47bcdeef87553b959ebb7dda3a6ca2354`
- `tests/test_r2_b_modes.py`：`6fb164f98951720fa4688b3695e2d45a4a61f39ff0074effe980bfafbe2eef73`
- `tests/test_r2_b_diff.py`：`84b7d40a275c7580b6e58e211dde2de65b9b7b26c7bd2cc15f13164b4fcce572`
- `tests/test_r2_b_risk.py`：`d8e6cc96d098d29717f96cb32d37642804da82990b2b51d573bac3555f136b78`

Batch C 继续冻结，直至独立 follow-up 明确 ACCEPT。

