# 医学监查风险投影 linked-view 形状边界（2026-08-02）

## 目的

继续审查项目→中心→个例风险投影与 Timeline/Profile/AE/LB/PD 联动边界，确保错误的
`linked_views` 不会因 truthy/falsy 回退被静默接受或绕过严格对象校验。

## 修订

- `linked_views`/`linkedViews` 现在按“显式 snake_case 优先”读取；若 snake_case 字段存在但为
  `false`、字符串或数组，即使 camelCase 同时提供合法值，也 fail-closed，不做错误回退。
- `null`/缺失仍表示没有联动视图；各联动 ID 仍必须是非空字符串数组，重复值稳定去重排序。
- 该修订保持项目/试验/中心/个例身份、风险去重、三级 rollup、progressive disclosure 和只读性质；
  不从图表或画像反推临床事实，联动仅消费已确认的风险证据。

## 验证

- `medicalMonitoringRiskProjection.test.mjs`：**16 passed**。
- 医学监查全部 **16 个 Node `.test.mjs` 文件通过**。
- 前端监查/统一风险/Timeline Python 合同：**52 passed**。
- `npm run build`：Vite **1919 modules transformed**，成功；仅保留既有 bundle >500 kB warning。
- 源/test/build SHA-256：
  - `frontend/src/features/medical-monitoring/medicalMonitoringRiskProjection.mjs`：`ccc5588df6adf404dd42133a527cc233088d3774329207198fa92b728e0d30f6`
  - `frontend/src/features/medical-monitoring/medicalMonitoringRiskProjection.test.mjs`：`dde0869b2751ac1561952cfe3b5ff1c9e7ad6920618233d29a8508b7dba58c06`
  - `frontend/dist/index.html`：`1a19408e84ea7e02acd46139baac7abf6fe3ba435487d572e375a24d2f9e582b`
  - `frontend/dist/runtime-build.json`：`bfb956e33183921e32b67242d1e512453c099b12fb23769276da6e7c58c937bf`

## 边界

- 仅离线纯函数、Node/Python contract 与生产构建；未启动 8911/5174、API、provider、浏览器或真实项目，
  未读写权威 SQLite，未触碰 18911/PID 43191、医学写作或其他并行模块。
- B6 仍为 `pending_review`（5 candidates/0 outcomes/2 blockers），C13 仍 blocked；不解锁任何
  reviewer outcome、source lineage revalidation、aggregate/CAS、迁移、事件创建、投影激活或商业发布。

