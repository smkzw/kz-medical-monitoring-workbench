# 医学监查 R5-S7 最终测量检查点（2026-08-27）

状态：`PAUSED_NO_LOSS_EXTERNAL_REPLAY_PENDING`

## 当前结果

R5-S7 的 Codex 浏览器、身份、网络与性能测量已经闭合；R6 外部报告审阅与三模式输出合同 v0.1 也已接受用于 synthetic/offline planning。R5-S7 尚未总关闭，唯一剩余门是 HY3(max) 原会话的最终聚焦重放。

## 本次完成的产品纠偏

1. 点击高密度医学旅程事件时，同步 event/visit/risk anchor/risk key/risk instance；无风险绑定事件会清除旧风险身份，不再携带陈旧实例导致 409。
2. 合成高密度 fixture 的事件与风险锚点统一为同一三位编号；`risk_ref` 恢复为逻辑风险键，与 `risk_instance_ref` 分离。
3. journey/profile/timeline 的本地指针切换复用同一受试者只读载荷，不再重复下载完整受试者数据；选择状态即时可见并使用 transition 完成非紧急更新。
4. 后端合成 authority packet 缓存；大体积 R5 响应直接使用 ORJSON，避免递归编码延迟。
5. 受试者 workspace 不再为无关唯一来源位置注入错误 identity。

## 决定性验证

- Python 聚焦回归：19 passed。
- 前端产品合同通过；route state 28 passed；adapter 41 passed。
- Vite production build 通过，仅有既有大 chunk warning。
- 最终测量：26/26 行通过，26 张截图；identity trace 36 条；network ledger 140 条且全部 GET、0 失败、0 外部请求、0 非 GET。
- 性能：cold p95 969.56 ms（门 2500）；warm p95 953.22 ms（门 1500）；交互 p95 44.60 ms（门 100）；FPS p05 107.53（门 30）；首屏最大 964 ms（门 10000）。
- 浏览器 console errors/warnings、page errors 与 failed requests 均为 0。
- 医学写作保护面按冻结算法复算：542 files，aggregate SHA-256 `feef0f171e6c102e56c930de57afb2cfaf78e7bfacc33f17d1fa8cfb7cb3d1ca`。
- 8911、5174 均无 LISTEN listener。

## 关键文件哈希

```text
96aa9754c10f52eb4c5605de4a07c1761aafaeb18572198afc63f554a2bf7679  services/api/app/medical_monitoring_r5_product_adapter.py
130e963af034c5e983197b095d9183b2d9eb657fcc87ddceeb5d17958b32fd3b  services/api/app/medical_monitoring_r5_product_router.py
2d62d6ac9d2bdc5db5670ac796bf69531189d6855cc0ea308001077620e50303  tests/test_medical_monitoring_r5_product_adapter.py
cee0f3f748cb718cf16c1a9ff83e755b5f67d2e735c3db398259016e3bf2fd83  frontend/src/features/medical-monitoring/r5/MedicalMonitoringR5Page.jsx
dd3d91d74f81ead49507f30e5947c554552c471b7e5d455aa00c4e3230979b4d  frontend/src/features/medical-monitoring/r5/medicalMonitoringR5ProductContract.test.mjs
a1ee0d9ddd50551dfd4be4b56888d16e64ce089404858dc472bdb1151813418d  artifacts/medical_monitoring_r5_s7_product_integration_browser_contract_v0_1/final_measurement_20260827/run_measurement.mjs
e617d245ee3058eddca70bb71abd577567b00f12acd13c1d64efb81dda1f01c4  artifacts/medical_monitoring_r5_s7_product_integration_browser_contract_v0_1/final_measurement_20260827/browser_matrix_results.json
5dd9417c2b55f0dfaaffaf9db02de9b37ccb380829d3bfb196ec0754dfde6845  artifacts/medical_monitoring_r5_s7_product_integration_browser_contract_v0_1/final_measurement_20260827/identity_trace.json
24e02eee975545848c8e64044fb1d9f1b68caee633861b33c7493a79301b55b7  artifacts/medical_monitoring_r5_s7_product_integration_browser_contract_v0_1/final_measurement_20260827/network_ledger.json
77565e1f90e093158af348b919dba030c5acd1364cc94862b7cdf41d4b084b0f  artifacts/medical_monitoring_r5_s7_product_integration_browser_contract_v0_1/final_measurement_20260827/performance_7x_cold_warm.json
3fbfdaaef65f32376782c858396abe8a986aa822f39e93abdeb651b637f5b792  artifacts/medical_monitoring_r5_s7_product_integration_browser_contract_v0_1/final_measurement_20260827/manifest.json
```

## 未完成边界

HY3 原 session `1d2324eb-0ec4-4466-a8e4-73c47aed9378` 在完成 B01、B04、B05、B06、B08、B10 后遭遇供应方 429；明确恢复时间为 2026-08-27 21:31:55 CST。当前时间早于恢复点，不能重放，也不得声称 HY3 已最终零缺陷。

## 下一次恢复动作

1. 先重新读取最新全局/工作台 AGENTS.md、本检查点、R5-S7 接受记录和 R6 合同接受记录。
2. 只读复核上述哈希、542 文件医学写作聚合哈希及 8911/5174 无监听。
3. 在 2026-08-27 21:31:55 CST 后，直接续接同一 HY3 session，完成 B11/B12/B13 和两视口最终结论；不得新建替代 session。
4. Codex 复核 HY3 原始证据。若满足合同且没有未处置问题，签发 `ACCEPT_R5_S7`；否则按问题最小纠偏、聚焦/相邻回归、Codex 浏览器复核后再在同一会话重放。
5. R5-S7 总关闭后，才进入已接受 R6 合同下的第一条 synthetic/offline runtime 纵切；继续不读取真实项目、不触碰医学写作、不做系统安全专项。
