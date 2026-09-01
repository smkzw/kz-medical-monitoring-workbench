# R4-D09 runtime 最终接受记录（2026-08-16）

## 结论

R4-D09“中心重复模式与系统性风险”179-case synthetic/offline runtime 已完成
合同、显式事实、deterministic evaluator、中文 Query、热点受试者、来源跳转、
可见性隔离、R2 handoff、mutation/replay/closure 和全量回归闭环。

独立只读复核最终返回 `ACCEPT_D09_RUNTIME`。权威复核与完整 SHA/证据见：
`runs/review/medical_monitoring_r4_d09_runtime_final_review_20260816.md`。

## 接受范围

- D09 仅拥有单中心重复个体风险、系统性数据/流程缺口及同中心时间趋势；
  不反向改写 D01-D08，不生成跨中心/项目级 D10 结论。
- 用户投影只使用权威 evaluator 结果；隐藏成员、工程标识、内部状态和伪造
  Query/R2 身份不得进入用户面。
- Query 为“依据 + 发现 + 行动项”的中文草稿；PD 仅在精确结构化事实与
  policy 双门满足时出现，不发送、不跟踪外部回复。

## 门禁

- D09 `243 passed + 33 subtests`；D07/D08 `1604 passed`；全 R4
  `4086 passed + 33 subtests`；R1/R2/R3 `327/598/339 passed`。
- artifact `99 passed`，registry/oracle checks 通过；Ruff、compile、fresh import
  通过；独立 reviewer 224 组注入挑战通过；8911 `STOPPED`。

## 下一安全动作

只解锁 R4-D10 项目/跨中心安全与疗效信号聚合的外部模式调研、owner 边界、
typed contract、挑战矩阵与冻结证据设计。D10 contract 接受前不得写 D10 runtime；
R5/UI、产品服务、真实项目/数据/模型、生产、医学写作与安全设计/测试继续冻结。
