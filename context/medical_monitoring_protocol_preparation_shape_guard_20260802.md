# 医学监查方案准备状态形状防护（2026-08-02）

## 目的

方案原文结构化是规则治理和后续日常监查的前置入口。方案版本、主题、候选、证据和条款类型
payload 若为 malformed，必须停止候选展示/状态机推进，不能因 `|| []` 或 scalar 迭代把异常数据
误当成“没有候选”。

## 修订

- 新增 `normalizeProtocolPreparationStatus`，严格校验根状态、topics、candidates、allowed fact
  types 和 job 对象；API 读取与启动响应统一经过同一 guard。
- `confirmedProtocolVersions`、polling/progress/start action、accepted facts、candidate evidence、
  fact type options 和 candidate decision reducer 对 malformed arrays fail-closed。
- 方案候选证据只接受显式字符串 evidence IDs 和对象数组；不会从 scalar 或字符迭代补造证据。
- 保留项目版本、source revision、candidate input revision 和用户决定流程；本切片没有放宽接受条件，
  没有创建事实、规则或风险。

## 验证

- 医学监查全部 **17 个 Node `.test.mjs` 文件通过**；方案准备模型 **29 passed**，project-switch
  isolation **30 passed**；既有 API/Models/RiskProjection/SubjectModels 套件均通过。
- 前端监查/统一风险/Timeline Python 合同：**54 passed**。
- `npm run build`：Vite **1920 modules transformed**，构建成功；仅既有 bundle >500 kB warning。
- SHA-256：
  - `frontend/src/features/medical-monitoring/medicalMonitoringProtocolPreparation.mjs`：
    `c4c7fbe0d4f2aab0cb4960bb9f1831e35f6df167e03f460b50709c5c4abe62fd`
  - `frontend/src/features/medical-monitoring/medicalMonitoringProtocolPreparation.test.mjs`：
    `d9c684f264a796eb0b65ce5c775673676d85d3273328568474f8265186b3a4d1`
  - `frontend/src/features/medical-monitoring/MedicalMonitoringProtocolPreparationPanel.jsx`：
    `e1f666a3cc4648405a1b8b86e66e1dd39189a6b5a95854eb0d23a90f7507e85e`
  - `frontend/src/features/medical-monitoring/medicalMonitoringProjectSwitchIsolation.test.mjs`：
    `3bd30e006addd19c7ba1129ab83a3aad2c47a9b6a4ab0f368d06c466469d2ada`
  - `frontend/dist/index.html`：
    `c72feed4ff8c3b42eab1bddf53dcb9a975a68bd15e0efdaac06a9c8dc7021e2e`
  - `frontend/dist/runtime-build.json`：
    `32383436bb9a720132f084ff550e6186f0e72b15ca9989aa7b92157e24af0ef7`
  - `frontend/dist/assets/index-D9idWxNI.js`：
    `16a1b21ec76da356d59231040df644698785dce379b4bb5f773b00c5fbbe00f5`

## 边界与下一动作

- 仅修改方案准备的只读状态消费与测试；未调用 API/provider、浏览器或真实项目，未启动 8911/5174，未
  读写权威 SQLite，未触碰 18911/PID 43191、医学写作或其他并行模块。
- B6 仍为 `pending_review`（5 candidates/0 outcomes/2 blockers），C13 仍 blocked；本切片不解锁
  reviewer outcome、source lineage revalidation、aggregate/CAS、迁移、事件创建、投影激活或商业发布。
- 下一安全动作仍是取得 hash-bound 授权 reviewer outcome，随后按顺序完成 aggregate/source-token
  replay 与 approved-input 内存 dry-run；在此之前继续只做同一数据流的离线 contract hardening。
