# R5-S7 产品最小接入与真实浏览器合同 v0.1 接受记录

Decision: `ACCEPT_R5_S7_CONTRACT_V0_1`

日期：2026-08-26 CST

## 接受范围

接受 R5-S7 的产品最小接入、只读 API、中文用户语义、Patient Journey、多视口 Playwright、性能、console/network、医学写作保护及 8911 临时生命周期合同。

这只解锁后续产品实现；不代表产品源码、浏览器、性能、视觉、真实项目、模型、临床结论或 S7 总体验收完成。

## 冻结字节

- 合同：`reviews/medical_monitoring_r5_s7_product_integration_browser_contract_v0_1_20260826.md`
- 合同 SHA-256：`767aa5ab127f383e504178dc71bd02684b931e1afc67a8e82aa8d6af57a5aba8`
- 矩阵：`artifacts/medical_monitoring_r5_s7_product_integration_browser_contract_v0_1/browser_acceptance_matrix.json`
- 矩阵 SHA-256：`6a5f8db3146ab170d1c186bd3478a3c98955070883a5e81b18383800c721ab7e`

## 决定性证据

- 矩阵为 `planned_unmeasured`，26 条唯一 row，覆盖 13 个状态及 1440×900、1600×1000 两个桌面视口；T1–T6、截图 id、console/network evidence id 均闭合。
- B08 高密度性能 profile 明确绑定 S6 1000 事件、40 指标、300 风险锚点语料及 7 次冷/暖测量。
- URL/canonical/API identity 方言和浏览器公共 target 到完整 27 字段 `identity_trace` 的映射闭合。
- 医学写作保护清单为 542 个文件，aggregate SHA-256 `feef0f171e6c102e56c930de57afb2cfaf78e7bfacc33f17d1fa8cfb7cb3d1ca`。
- 8911、5174 均无 listener。
- 同一独立 reviewer 两次指出闭合缺陷，修订后对当前字节返回 `ACCEPT_R5_S7_CONTRACT_V0_1`。

## 下一动作

另开受治理的 S7 产品实现 execution，严格按闭合 allowlist 修改最小前后端接线并先完成离线聚焦/相邻回归和 production build。浏览器 execution 与独立视觉/医学 conference 必须分离；在浏览器 execution 前 8911 继续停止。
