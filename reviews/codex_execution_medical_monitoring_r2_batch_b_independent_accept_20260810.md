# R2 Batch B 累积独立验收

日期：2026-08-10

判定：`ACCEPT`（仅 synthetic/offline Batch B）

## 接受对象

接受 `poc/medical_monitoring_ai_native_r2/` 当前冻结快照中的 Batch B：风险候选/实例/追加式生命周期与裁决、稳定身份与 merge/split、双基线、三类 ModeContract、full/incremental diff，以及 SAE/AESI 识别和自动关闭边界。

该结论由独立复核系列累积形成：follow-up 03 独立重放历史 P1/P2、merge/split、ModeContract、diff 与原子失败路径，只留下中文明确否定误报；follow-up 04 确认该误报已修复并发现不确定语境漏拦截；follow-up 05 最终确认不确定/双重否定、明确缺如和混合句全部符合，且全量既有回归未缩减。历史 VETO 均保留，不被本 ACCEPT 覆盖。

## 决定性证据

- 风险聚焦：`148 passed`。
- Batch B：`257 passed`。
- R2 全量：`493 passed`。
- 内存编译：21 个 Python 文件通过。
- cache：无；TCP 8911 listener：无。
- 独立真实对象矩阵：12 个不确定/双重否定变体均形成 SAE/AESI 标记并拒绝机器关闭；11 个明确缺如表达均无标记并合法关闭；4 个混合句均保留未否定风险。

独立终态报告：`runs/medical_monitoring_r2_batch_b_independent_followup_05_20260810.md`。

## 冻结锚点

- R2 内容清单：`ecf9d07df74fc3ff6a2d775a91683de24a6db2eecf77e6a6ad3f4f9ec02e064f`
- `src/mm_r2/risk.py`：`25c6b7cc8932cdf3c28a245679449c8c35b2653492f8fa2a7b75516f8fbc0f8b`
- `tests/test_r2_b_risk.py`：`055ed316dcf8e6c4544058508b4d773f7e4d0d9085126ef6b823223f70dd05dc`
- 独立报告文件 SHA-256：`93744a0662790835d9dbde80b223ac6ebf1db39bcdcb14fe21e710eac23014ee`。

Batch A ACCEPT 仍是不可变先决历史。后续修改若触及 Batch A/B 合同，必须按传播范围重验；不得静默改写本次接受对象。

## 边界与下一步

该 ACCEPT 不代表 Batch C、R2 总体、产品、真实项目或生产验收。用户已明确不需要额外系统安全设计或安全测试；下一步只实现用户功能必需的最小持久化、原子保存/恢复、发布读取一致性和 R1 只读兼容，不扩展攻防或安全专项，随后直接进入 Patient Journey 与监查看板阶段。
