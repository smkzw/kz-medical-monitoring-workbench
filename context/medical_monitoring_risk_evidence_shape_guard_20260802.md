# 医学监查风险来源证据形状防护（2026-08-02）

## 目的

为项目→中心→个例风险下钻和来源证据工作区保持 fail-closed 语义，禁止
malformed `evidence_span_ids`、`source_refs` 或 `tags` 在前端投影中被当作可用数组，或因
`.map`/`.forEach` 形状错误导致风险证据工作区崩溃。

## 修订

- `monitoringRiskRowsFromInbox` 与 `riskIndexRowsFromApi` 现在只接受显式字符串数组和对象数组；
  scalar、布尔、数字成员或错误对象形状降级为空数组，并标记 `sourceEvidenceShape=malformed`。
- API 风险投影同时校验 evidence locators、work-item source refs 和 legacy inbox source refs；任一
  来源证据形状异常都不会生成有效来源证据。有效 work-item source refs 保留在最终风险行，不能被
  legacy inbox 空数组覆盖；去重、风险身份和处置字段保持不变。
- `riskSourceGroups` 对来源引用与 evidence locator 再做数组/对象防御；风险证据工作区显示明确的
  “来源证据字段形状异常，未按有效证据展示”告警，不把 malformed payload 静默渲染成事实。
- inbox/risk-index 根级 `items` 与 inbox rows 也必须是对象数组；scalar/混合数组现在返回空投影，
  不会在风险列表初始化时触发 `.map/.forEach` 崩溃。
- 风险行的 `id`、`riskId`、`riskKey` 只接受非空字符串；malformed identity 直接从只读投影剔除，避免
  产生不可定位或 React key 不稳定的风险项。
- source-ref 对象内部的 `source_type`、`locator`、`label`、`source_id` 若显式存在也必须是非空字符串；
  错误 locator 不会被正则或字符串插值伪装成可打开证据。
- 本切片只改善只读展示边界，不推断医学意义，不写风险权威，不改变 B6/C13 authority gate。

## 验证

- `medicalMonitoringModels.test.mjs`：**55 passed**。
- 医学监查全部 **16 个 Node `.test.mjs` 文件通过**（Models 49 passed）。
- 前端监查/统一风险/Timeline Python 合同：**52 passed**。
- `npm run build`：Vite **1919 modules transformed**，成功；仅保留既有 bundle >500 kB warning。
- 源/test/build SHA-256：
  - `frontend/src/features/medical-monitoring/medicalMonitoringModels.mjs`：`1490850e157a31556b49b48f99388aedc6366b4c949c78bf0705e265e07d8a0b`
  - `frontend/src/features/medical-monitoring/medicalMonitoringModels.test.mjs`：`d1072aa583d3441546c137665da0f75c2c5b6eaf8f7a7cf1adcb6604d7bcfb4d`
  - `frontend/src/App.jsx`：`a0afb472a8d9849e4a1c125b6bc7c23a8d49ac99b28b8416771c29ff0ed56b5e`
  - `frontend/src/styles.css`：`bf0d2a6aaf6576072c67bbbb43387289b5bd9732b7a3bd8b0443878b1e0538a6`
  - `tests/test_frontend_unified_risk_workbench_contract.py`：`6427c8c8e22c9f9f7e610f2aec1e267db9b364305dbe3094802733ddd31183cc`
  - `frontend/dist/index.html`：`5276637426e65c5de40231d87675a0b83812dd74ed121316ffc5ea92de5a2355`
  - `frontend/dist/runtime-build.json`：`bfb956e33183921e32b67242d1e512453c099b12fb23769276da6e7c58c937bf`

## 边界

- 仅离线纯函数、Node/Python contract 与生产构建；未启动 8911/5174、API、provider、浏览器或真实项目，
  未读写权威 SQLite，未触碰 18911/PID 43191、医学写作或其他并行模块。
- B6 仍为 `pending_review`（5 candidates/0 outcomes/2 blockers），C13 仍 blocked；本切片不解锁
  reviewer outcome、source lineage revalidation、aggregate/CAS、迁移、事件创建、投影激活或商业发布。
