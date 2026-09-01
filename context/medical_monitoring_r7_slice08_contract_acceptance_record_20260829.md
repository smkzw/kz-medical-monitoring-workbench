# R7 Slice-08 三模式跨 Run 连续性合同接受记录

日期：2026-08-29  
状态：`FROZEN_ACCEPTED_R7_SLICE_08_CONTRACT_V0_2`

## 接受对象

- 核心合同：`reviews/medical_monitoring_r7_slice08_three_mode_carry_forward_contract_v0_1_20260829.md`
- 纠偏附录：`reviews/medical_monitoring_r7_slice08_three_mode_carry_forward_contract_v0_2_20260829.md`
- 冲突时 v0.2 优先；v0.1 的旧状态为被纠偏证据，不得单独实施。

## 关键决定

1. 数据缺失不等于风险消除；高危/严重风险缺行不得自动关闭。
2. R2 风险生命周期仍是唯一机器权威；R7 只生成七类中文变化投影。
3. listing 行和 Journey/SVG 不作为沿用产物；Journey 每轮从当前 R5 权威事实重新投影。
4. 沿用必须核对同项目/同模式已发布基线、publication 成员、artifact 字节 SHA-256、对象身份和规则适用性。
5. v3 迁移只新增 continuity plan/item 两表，复用现有 ResultPublication CAS，不建立第二发布器或风险 transition 表。
6. 日常模式推荐最近兼容基线并允许改选；锁库前只 full 且 Query 归因必须有证据；核查前强制 fixed total，新数据/规则创建新运行。
7. 未确认或过期特殊规则失败关闭；Query 草稿保持风险/受试者/中心单项绑定并在项目输出包聚合。

## 会商与 Codex 复核

- Gemini 3.7 Flash high 同一 session Round 1 `REVISE`、Round 2 `ACCEPT_R7_SLICE_08_CONTRACT_V0_2`，无 fallback。
- Codex 亲自核对 R1 高危缺行、R2 生命周期、R6 carry-forward/fixed-total 和 R7 迁移/CAS 源码后冻结合同。

## 边界

本记录只接受 Slice-08 合同，不接受任何实现、真实项目/模型医学质量、R7 总体、R8、商业化或监管结论。医学写作未修改；8911/5174 保持停止。

## 下一安全动作

只解锁 08A：实现 stdlib-only continuity 领域对象、v2→v3 additive migration、计划生成/校验、确定性与故障矩阵。不得提前改 UI 或运行真实项目。

