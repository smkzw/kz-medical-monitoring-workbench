# R2 Batch B 独立 follow-up 03 VETO 纠偏门

日期：2026-08-10

状态：`REMEDIATED / PENDING_SAME_SESSION_INDEPENDENT_REVIEW`

来源：`runs/medical_monitoring_r2_batch_b_independent_followup_03_20260810.md` 的唯一 P2。既有 VETO、纠偏与 Batch A ACCEPT 均作为不可变历史保留；Batch C 继续冻结。

## 根因与纠偏

原中文术语判断只支持一组紧邻术语的固定否定前缀，既不覆盖“没有发生、未有、不含、不包含、无任何”等明确否定，也不检查术语后的“不存在”，因此普通风险会被误标为 SAE/AESI，并被高风险关闭门错误阻断。

本轮把这条平面前缀表收敛为有限的中文否定语法边界：

- 术语前只接受明确的否定、缺如、未发生/未发现与排除性表达；
- 术语后只接受句末或标点前的“不存在、未发生/未出现、没有发生/没有出现”等明确否定；
- 同一句有多个术语时逐个判断，任一未被否定的 SAE/AESI 仍形成风险标记；
- “未报告、未排除、没有排除、疑似”等可能代表漏报或尚未排除风险的表达，明确保留为风险阳性，避免用消除误报的方式制造漏报。

## 新增决定性回归

- 32 类普通词、英文否定和中文明确否定进入真实 `RiskInstance`，其中覆盖 follow-up 03 的全部失败例与相邻表达；均保持无 SAE/AESI 标记，并经真实 coverage/adjudication/close 路径完成低风险关闭。
- 18 类 SAE/AESI 阳性表达进入真实 `RiskInstance`，新增“未报告严重不良事件、没有排除严重不良事件、未排除特别关注不良事件、疑似特别关注的不良事件”；均形成对应标记并被真实机器关闭门拒绝。
- 原有 merge/split、裁决、coverage、ModeContract、diff 与 Batch A 回归未缩减。

## 决定性检查

- 风险聚焦：`133 passed in 0.14s`。
- Batch B：`242 passed in 0.24s`。
- R2 全量：`478 passed in 0.33s`。
- 内存语法编译：21 个 Python 文件通过。
- R2 cache：0；TCP 8911 listener：无。

## 冻结锚点

- R2 内容清单：`97da1750c217c98c521ad737ecfea3d147257478a2af83325b4ca86a1b0e46b4`
- `src/mm_r2/risk.py`：`549f21812ec77c13985da5836714dd7753c337787fe5bde50d2d28bde564893f`
- `tests/test_r2_b_risk.py`：`f9dfeb1a61594257c5ea202872da26a451d209f6d2dfaf586ad1b224749f6362`
- 其余八项 Batch B 审阅工件 SHA 与 follow-up 03 开始快照一致。

本轮仍只属于 synthetic/offline Batch B。持久化、跨进程身份、真实用户事件与电子签名语义未验证，属于 Batch C/产品层边界。只有原独立 Luna 会话 follow-up 04 明确 `ACCEPT` 后，Batch B 才可冻结并解锁 Batch C。
