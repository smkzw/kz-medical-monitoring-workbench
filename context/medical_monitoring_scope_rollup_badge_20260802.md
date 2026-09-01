# 医学监查项目/中心/个例待行动计数选择（2026-08-02）

## 目的

保证页面“待行动”徽标与用户当前选择的项目、中心或个例范围一致，避免后端已提供
中心/个例 rollup 时仍把试验级总数显示在窄范围页面。

## 修订

- `MonitoringPage` 现在按当前 `riskScope` 读取 `riskIndex.rollup.trial`、`rollup.sites[]` 或
  `rollup.subjects[]`，使用对应 `scope_id` 的 `needs_action_count`。
- 中心/个例 rollup 缺失时才回退到当前已加载风险行的显式 `needsAction` 计数；不按严重度、标题或自由文本推断。
- `sites`/`subjects` 仅在显式数组形状通过时才查找；malformed rollup 不会在切换范围时触发页面异常。
- 查询参数、风险事实、处置状态、导出和 authority gate 均未改变；修订只影响只读数量显示。

## 验证

- 医学监查全部 **16 个 Node `.test.mjs` 文件通过**（Models 52 passed、RiskProjection 16 passed）。
- 前端监查/统一风险/Timeline Python 合同：**53 passed**。
- `npm run build`：Vite **1919 modules transformed**，成功；仅保留既有 bundle >500 kB warning。
- 源/test/build SHA-256：
  - `frontend/src/App.jsx`：`3346d9457805eb69bbeb8897fc9112ae809feecc1e45a6d7c50ce3b9190c9f61`
  - `tests/test_frontend_unified_risk_workbench_contract.py`：`d0821d7af8acb653b442009fe975def0882af217c567b00ec9dde13db53b8e63`
  - `frontend/dist/index.html`：`ea7a384a2451e367e53645fb8145691c960e29df570e5063c64f10a5b590297a`
  - `frontend/dist/runtime-build.json`：`921f2a8d5fef4c036c216af6c1e9342ec0b0ec4dbd16b5cc4d8c0648f92cd142`

## 边界

- 仅离线 UI 读取选择、契约测试和生产构建；未启动 8911/5174、API、provider、浏览器或真实项目，
  未读写权威 SQLite，未触碰 18911/PID 43191、医学写作或其他并行模块。
- B6 仍为 `pending_review`（5 candidates/0 outcomes/2 blockers），C13 仍 blocked；不解锁任何
  reviewer outcome、source lineage revalidation、aggregate/CAS、迁移、事件创建、投影激活或商业发布。
