# R7 Slice-08A 跨 Run 连续性基础接受记录

日期：2026-08-29  
状态：`ACCEPT_R7_SLICE_08A_SYNTHETIC_OFFLINE_FOUNDATION`

## 接受范围

- 新增标准库 `continuity.py`，冻结 `DecisionBaseline`、`CarryForwardPlan/Item`、
  `RiskChangeKind`、逐对象处置、规则作用域及 canonical digest。
- R2 仍是唯一风险生命周期；R7 只投影新增、升级、持续、降级、关闭、重开、需重新判断。
- 缺行/删除不自动关闭；非日常模式仅允许全量计划；Query 仅草稿状态可沿用。
- `launch_registry` 以 v2→v3 additive migration 增加 continuity plan/item 两表，并通过
  既有 `ResultPublication` CAS 在同一事务内完成 plan published 与结果 available。

## 决定性证据

- 聚焦/相邻：63 passed；完整 R7：220 passed；产品医学监查：256 passed。
- 9-cell：3 个 `PYTHONHASHSEED` × normal/`-O`/`-OO`，每格 24 passed。
- v2→v3 七个故障注入点、关闭重开、重复保存冲突、摘要漂移与发布回滚通过。
- execution audit、execution review-gate、独立 conference review-gate 均通过。
- 独立会商：`Pi/google-antigravity/gemini-3.7-flash:high`，无 fallback；Codex 纠正了
  “三项 authority 字段均已强制 SHA-256”的过度陈述。
- 8911/5174 停止；未运行真实项目/真实模型，未修改 UI、R1-R6 或医学写作。

## 明确保留边界

- `r6_publication_digest` 当前仅以既有 `ResultPublication.publication_fingerprint` 作为 08A
  synthetic 代理；真实 R6 ModeOutput 指纹同构尚未验证。
- `artifact_verified` / `artifact_member_verified` 当前是 fail-closed 元数据门，不是实际字节
  读取或 publication 成员集复核。
- 真实 R5 authority bridge、R6 ModeOutput 子项抽取、artifact 实际字节 SHA-256 与 member-set
  校验属于 Slice-08B/08D；08A 不代表 Slice-08、R7、R8 或医学质量完成。

## 下一安全动作

先冻结 Slice-08B 窄合同，再接入真实 R5 authority identity、R6 ModeOutput 子项提取及
publication artifact member/byte verification；保持服务和真实项目停止，不改 UI。
