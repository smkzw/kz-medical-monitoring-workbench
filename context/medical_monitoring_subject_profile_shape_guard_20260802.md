# 医学监查个例 Profile/Timeline 形状防护（2026-08-02）

## 目的

按 Patient Profile 与 AE 风险联动的 source-grounded 要求，保护真实项目个例页面不因 API
返回的 malformed 数组/字段崩溃，也不把错误 payload 当成临床事实、风险或时间线关联。

## 修订

- 新增只读 `normalizeMonitoringSubjectProfile` 边界：`timeline`、疗效/安全性 trends、risk prompts、
  review focus、domain availability 和 nested subject context 只接受预期数组/对象形状；异常项被
  移除并记录 `profile_shape_warnings`，不补造日期、范围、疗效、AE 或响应结论。
- Timeline 事件与趋势点的 `related_risk_ids` 只接受非空字符串数组；`risk_flag`、`is_baseline`、
  `is_unscheduled`、`ongoing` 只接受显式 boolean。错误值不会以 truthy 字符串触发风险着色或 exact-focus。
- App 在构造 subject view 前使用同一归一化结果；Timeline/Profile 顶部明确显示异常字段和“请回到来源证据核查”，
  保留空态/不可用状态而不是声称“无风险”。
- `capability_mode=restricted` 与 `capability_limitations` 在 Timeline/Profile 顶部显式显示；受限映射的空态不再
  被误读为“没有风险”或“数据已完整”。非法 capability 状态 fail-closed 为 restricted 并记录 shape warning。
- 本切片只读、无临床推断、无权威写入；没有改变 B6/C13、风险处置或来源证据权限边界。

## 验证

- `medicalMonitoringSubjectModels.test.mjs`：通过（含 malformed profile、关联风险 ID 和 boolean 防护）。
- 医学监查全部 **16 个 Node `.test.mjs` 文件通过**（Models 50 passed、SubjectModels passed）。
- 前端监查/统一风险/Timeline Python 合同：**53 passed**。
- `npm run build`：Vite **1919 modules transformed**，成功；仅保留既有 bundle >500 kB warning。
- 源/test/build SHA-256：
  - `frontend/src/features/medical-monitoring/medicalMonitoringSubjectModels.mjs`：`5e46ff7f70f6b04da2c8b38479342cf1296d1e51eb9e36033c8a329b563e480b`
  - `frontend/src/features/medical-monitoring/medicalMonitoringSubjectModels.test.mjs`：`8a502121688c9b5585d455177695413eba7b4e2f0b581648c5c194aee8040aa7`
  - `frontend/src/features/medical-monitoring/MedicalMonitoringSubjectViews.jsx`：`6cb55fad653b112d700e4249db787c4e0b177d1bfe2bab409f1597472b29998f`
  - `frontend/src/App.jsx`：`ef430f41e44c9feb93c8ef2b4f54e853120fa88e90012fe5957ddd39d4384dfb`
  - `frontend/src/styles.css`：`f7020f5803e0c4a560a5614b525daff1a056f0201cc4f342f4e11fc1b3805479`
  - `tests/test_frontend_unified_risk_workbench_contract.py`：`34c8d5b792483bc39852ee985efdb7aa4a53882ba1f2a4a7f0cd4c6df0ef45c7`
  - `frontend/dist/index.html`：`a06f04179ff73c988477efa2b4a17b843979405dc7684d24dd483da67d6bffa2`
  - `frontend/dist/runtime-build.json`：`0f9a8263979e065f97c4eebc325e64fbf09326c830cdb4fef3e6e954b2ee82e5`

## 边界

- 仅离线前端模型/视图/契约测试与生产构建；未启动 8911/5174、API、provider、浏览器或真实项目，
  未读写权威 SQLite，未触碰 18911/PID 43191、医学写作或其他并行模块。
- B6 仍为 `pending_review`（5 candidates/0 outcomes/2 blockers），C13 仍 blocked；本切片不解锁
  reviewer outcome、source lineage revalidation、aggregate/CAS、迁移、事件创建、投影激活或商业发布。
