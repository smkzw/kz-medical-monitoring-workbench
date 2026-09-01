# R5-S7 产品集成运行时 v0.1 验收记录

日期：2026-08-26

## 结论

R5-S7 离线产品集成运行时接受。独立 verifier 最终结论为 `ACCEPT_R5_S7_PRODUCT_RUNTIME_V0_1`。

该结论只覆盖冻结合同下的后端只读投影、GET-only 路由、前端产品页面/适配器/路由状态及离线跨层闭环，不等于浏览器、视觉、真实服务、真实项目、真实模型或医学结论接受。

## 合同锚点

- 合同：`reviews/medical_monitoring_r5_s7_product_integration_browser_contract_v0_1_20260826.md`
- 合同 SHA-256：`767aa5ab127f383e504178dc71bd02684b931e1afc67a8e82aa8d6af57a5aba8`
- 浏览器矩阵：`artifacts/medical_monitoring_r5_s7_product_integration_browser_contract_v0_1/browser_acceptance_matrix.json`
- 矩阵 SHA-256：`6a5f8db3146ab170d1c186bd3478a3c98955070883a5e81b18383800c721ab7e`

## 决定性证据

- 后端聚焦 `22 passed`，verifier 相邻 `150 passed`。
- 前端三项聚焦测试通过：adapter 41 checks、route state 24 checks、产品合同通过；verifier 相邻 `41 passed`。
- Vite 生产构建成功，1960 modules transformed；仅有非阻断大 chunk warning。
- exact allowlist 16/16，extra=0，missing=0。
- source-evidence 使用表面特定投影；缺失/空 `current_risks` 均以 `CURRENT_RISKS_REQUIRED` fail closed。
- `counts.change_band_count` 权威计数直达页面模型；中心视图严格绑定 exact `site_ref`，无 nearest fallback。
- 8911 与 5174 无监听。
- 医学写作保护清单 542 files，aggregate SHA-256 `feef0f171e6c102e56c930de57afb2cfaf78e7bfacc33f17d1fa8cfb7cb3d1ca`。

## 独立审阅与未解锁范围

- verifier session：`01a03cc9-b807-7db3-bdd5-2a92eb7159ca`
- 最终报告：`runs/execution/mm_r5_s7_product_integration_runtime_v0_1_20260826/worker_03.md`
- 浏览器、视觉和真实服务运行仍为 pending。恢复时必须先复核本记录与当前文件字节，再建立单独的浏览器/视觉 acceptance packet；在此之前保持 8911/5174 停止。
