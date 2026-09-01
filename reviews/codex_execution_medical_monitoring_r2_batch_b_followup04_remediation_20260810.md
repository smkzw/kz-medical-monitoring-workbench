# R2 Batch B 独立 follow-up 04 VETO 纠偏门

日期：2026-08-10

状态：`REMEDIATED / PENDING_FINAL_SAME_SESSION_REVIEW`

来源：`runs/medical_monitoring_r2_batch_b_independent_followup_04_20260810.md` 的唯一 P1。既有 VETO 与 Batch A ACCEPT 均保留为不可变历史；Batch C 继续冻结。

## 根因与最小纠偏

follow-up 03 的明确中文否定已正确识别，但实现仍以“术语前文本是否以没有等词结尾”为条件，导致“不能确认没有、疑似没有、可能没有、没有证据表明没有”等不确定或双重否定句被误当成明确缺如。

本轮不再追加一般性的否定词表，而是增加句界约束：

- 否定词只有位于句首/标点后的独立断言，或位于“截至目前、该受试者、研究期间、经核查”等受控中性上下文之后，才可把 SAE/AESI 术语判为明确缺如；
- 术语后的“不存在/未发生”等同样要求该术语所在分句此前只有中性上下文；
- “不能/无法确认、不能确定、疑似、可能、没有证据表明、并非没有、不一定没有”等不确定或双重否定上下文不满足中性门，因此继续形成 SAE/AESI 风险标记；
- 同一句多个术语逐个判断，明确缺如的一个术语不会掩盖另一个未排除或疑似术语。

该修改只处理临床风险语义准确性；未扩展任何系统安全设计或安全测试。

## 新增决定性回归

- 29 类 SAE/AESI 阳性表达走真实 `RiskInstance → coverage → adjudication → close`，新增 follow-up 04 的七个不确定语境、双重否定、后置否定的不确定语境及混合句；均形成对应风险标记并被机器关闭门拒绝。
- 36 类普通词、英文否定与明确中文缺如表达走同一真实对象链，覆盖“目前没有发生、截至目前尚未发生任何、该受试者无任何、经核查…不存在”等中性上下文；均保持无 SAE/AESI 标记并完成合法低风险关闭。
- 原有 merge/split、裁决、coverage、ModeContract、diff 与 Batch A 回归未缩减。

## 决定性检查

- 风险聚焦：`148 passed in 0.15s`。
- Batch B：`257 passed in 0.23s`。
- R2 全量：`493 passed in 0.34s`。
- 内存语法编译：21 个 Python 文件通过。
- R2 cache：0；TCP 8911 listener：无。

## 冻结锚点

- R2 内容清单：`ecf9d07df74fc3ff6a2d775a91683de24a6db2eecf77e6a6ad3f4f9ec02e064f`
- `src/mm_r2/risk.py`：`25c6b7cc8932cdf3c28a245679449c8c35b2653492f8fa2a7b75516f8fbc0f8b`
- `tests/test_r2_b_risk.py`：`055ed316dcf8e6c4544058508b4d773f7e4d0d9085126ef6b823223f70dd05dc`

仍只验收 synthetic/offline Batch B。若同一 Luna 会话 follow-up 05 明确 `ACCEPT`，即可冻结 Batch B；后续只实现用户功能所需的数据正确性/可恢复性底座，不另开系统安全设计或测试工作流，并尽快转入 Patient Journey 与用户看板阶段。
