# 医学监查项目—中心—个例风险投影严格身份边界（2026-08-02）

## 目的

为项目→中心→个例图形化下钻保持单一风险事实来源，禁止只读前端投影把 malformed
identity、evidence 或 linked-view payload 静默转换为可展示数据。

## 修订

- `risk_instance_id`、project/trial/scope identity、severity/status/source/rule/title 等必需身份
  字段只接受非空字符串；site/subject/trial optional identity 也拒绝数字、布尔和对象。
- evidence IDs、evidence locators、Timeline/Profile/AE/LB/PD linked views 必须是非空字符串数组；
  scalar、布尔、数字成员和错误 linked-view 对象 fail-closed。
- unread/needs_action 只接受显式 boolean；aggregate version 只接受非负整数；可选叙述/版本/更新时间
  字段不再用 `String()` 补造值。
- 保持风险实例去重、project/trial 混合阻断、三级风险身份守恒和 progressive disclosure；该层只读，
  不写风险权威、不推断医学意义、不替代 B6/C13 authority gate。

## 验证

- `medicalMonitoringRiskProjection.test.mjs`：**16 passed**。
- 医学监查全部 Node `.test.mjs`：**16 个文件全部通过**（含 RiskProjection 16 passed）。
- 前端监查/统一风险/Timeline Python 合同：**51 passed**。
- `npm run build`：Vite **1919 modules transformed**，成功；仅保留既有大 bundle warning。
- 源/test/build SHA-256：
  - `frontend/src/features/medical-monitoring/medicalMonitoringRiskProjection.mjs`：`abd30882d573f78404c0a45a39e14a9bd3d1829bde8a90e0780cd64b03254d43`
  - `frontend/src/features/medical-monitoring/medicalMonitoringRiskProjection.test.mjs`：`88748da1d820f0a0cf132a85db4e89f2fa35ca321ef1afb365e260b93059b813`
  - `frontend/dist/index.html`：`e3e3d6d855870a6796b4a11284b4ecc6f21dea60fece6078802e6d8c2c1c7cf3`
  - `frontend/dist/runtime-build.json`：`3232350ff9c17cb372ac9f251fd01ab0673539c72a56438d315cf038fb6c097b`

## 边界

- 只读纯函数、Node/Python contract 与离线 build；未启动 8911/5174、API、provider、浏览器或真实项目，
  未读写权威 SQLite，未触碰 18911/PID 43191、医学写作或其他并行模块。
- B6 仍需授权 reviewer outcomes、source-content lineage revalidation 与 aggregate/CAS replay；本切片
  不解锁迁移、事件创建、投影激活或商业发布。
