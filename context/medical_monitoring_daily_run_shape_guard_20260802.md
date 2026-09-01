# 医学监查日常运行状态形状防护（2026-08-02）

## 目的

日常医学监查状态机是风险发现、AI 复核、风险确认和下一批次比较基线的入口。它必须在 API
返回 malformed list/detail/step/count/baseline 时停止展示或停止推进，不得把异常计数当成零，也
不得把不确定的比较基线版本提交给确认接口。

## 修订

- 新增 `medicalMonitoringDailyRunView.mjs`，严格校验运行列表和详情的根对象、运行记录、活动运行、
  当前基线和步骤数组；异常形状返回 fail-closed 错误，不进入状态选择或渲染。
- newest-run 选择只接受同批次、非空 `run_id` 的对象；scalar/缺失 ID 记录不被当成活动运行。
- 风险计数只接受显式非负整数；缺失、布尔、数字字符串或负数不再显示为 `0`，而是提示打开风险清单
  核对计数证据。
- 比较基线为空时仍明确使用 CAS 初始版本 `0`；基线对象的 malformed revision 不生成“确认并设为
  比较基线”按钮，并显示阻断提示。
- AI 复核进度显示只接受显式非负整数；异常计数显示“待确认”，不伪造完成数。
- 运行列表/详情形状失败时清理旧 detail、AI progress 和 readiness，避免旧项目或旧批次状态继续可见。

## 验证

- 医学监查全部 **17 个 Node `.test.mjs` 文件通过**；新日常运行视图测试 **17 passed**，
  project-switch isolation 回归 **27 passed**；既有 Models 55、RiskProjection 16 等套件均通过。
- 前端监查/统一风险/Timeline Python 合同：**54 passed**。
- `npm run build`：Vite **1920 modules transformed**，构建成功；仅既有 bundle >500 kB warning。
- SHA-256：
  - `frontend/src/features/medical-monitoring/medicalMonitoringDailyRunView.mjs`：
    `423a1d08078ea66b2492abb4ffbc6ab0abca95f242ed20e5da8436a0bc59c509`
  - `frontend/src/features/medical-monitoring/medicalMonitoringDailyRunView.test.mjs`：
    `0749947f85ad661e9f5e30d8171292139c80aed24aee93a933da941c3db69f63`
  - `frontend/src/features/medical-monitoring/MedicalMonitoringDailyRunPanel.jsx`：
    `56bc94df8e660b0863c3eadd44d8f158b070e786c38edb98bab17fa1ed3ee427`
  - `frontend/src/features/medical-monitoring/medicalMonitoringProjectSwitchIsolation.test.mjs`：
    `07a046c7261ead354e2c8dc7cfd6b37359e66ee7306b0604267ba799659fba4f`
  - `frontend/dist/index.html`：
    `af97cb244164083355a1fc99889a60139d811f6ea67f8336ace8a2849235e5c3`
  - `frontend/dist/runtime-build.json`：
    `216b50b28c347558146fa87bffcf284aeab874f7af706ff1b543e6e762ceccec`
  - `frontend/dist/assets/index-PYDNh2Qc.js`：
    `64619f3b169a1c5b1003154004cebafa49c93f3430749884ea21b0b93c229ff1`

## 边界与下一动作

- 仅修改日常运行只读状态消费、形状模型与前端合同测试；未调用 API、provider、浏览器或真实项目，未
  启动 8911/5174，未读写权威 SQLite，未触碰 18911/PID 43191、医学写作或其他并行模块。
- B6 仍为 `pending_review`（5 candidates/0 outcomes/2 blockers），C13 仍 blocked；本切片不解锁
  reviewer outcome、source lineage revalidation、aggregate/CAS、迁移、事件创建、投影激活或商业发布。
- 下一安全动作仍是取得 hash-bound 授权 reviewer outcome，随后按顺序完成 aggregate/source-token
  replay 与 approved-input 内存 dry-run；在此之前继续只做同一数据流的离线 contract hardening。
