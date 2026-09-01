# 医学监查 Checklist 形状防护（2026-08-02）

## 目的

让项目→中心→个例风险 Checklist 在 API 返回 malformed rows、taxonomy、总数、锁定筛选或
可选刷新回调时仍保持简洁、可用且 fail-closed，不把异常值转换成可展示的医学事实。

## 修订

- `MedicalMonitoringRiskChecklist` 只渲染非空对象行；根级 scalar、数组成员 scalar 和 null
  均不进入表格、骨架屏或空态判断。
- taxonomy categories 只接受对象数组；过滤标签不再对 malformed category 调用字段访问。
- `total` 只接受非负整数；布尔、数字字符串、浮点和负数不参与分页或总数展示。
- `lockedFilterKeys` 只接受数组，旧快照“查看最新”通过可选回调安全调用；没有回调时不抛错。
- 保留既有明确空态提示，避免把“当前条件没有可展示行”误报为“项目无风险”。
- 新增 Python 静态合同，锁定上述边界，避免后续重构恢复 `rows.map`/`total` 直读。

## 验证

- 本轮重新读取最新全局与工作台 `AGENTS.md`；SHA-256 分别为
  `/Users/smkzw/.codex/AGENTS.md` `3659d0630df4e0094146917f67c2ce801f70d0eadd5b598469c7651c3bdf3ca3`、
  工作台 `31d8b1b6f1fb7c2dfb3be2dc9eaeca09c56a339b43f0def41c091af1a847b001`。
- 医学监查全部 **16 个 Node `.test.mjs` 文件通过**：Models 55、RiskProjection 16、SubjectModels
  tests passed，其余既有套件均通过。
- 前端监查/统一风险/Timeline Python 合同：**54 passed**。
- `npm run build`：Vite **1919 modules transformed**，构建成功；仅既有 bundle >500 kB warning。
- SHA-256：
  - `frontend/src/features/medical-monitoring/MedicalMonitoringRiskChecklist.jsx`：
    `7f8b5157b383a51e7ba424575fef7568f6d73aa897aa2a70e013b84a09b2c19f`
  - `tests/test_frontend_unified_risk_workbench_contract.py`：
    `799712b4fca369dd70f20d5b3570c7fae8454c2a1ca3240d7a418c6258d878e3`
  - `frontend/dist/index.html`：
    `e91644850d77ae3ce6b3d6f32943b9007acb10ba8289495682dcb3ae88f17b22`
  - `frontend/dist/runtime-build.json`：
    `6c526b8d0639db0d1e6b926f0ea700126fdc25029f78bb0cd5b786716ae99f22`
  - `frontend/dist/assets/index-CZFDl1BB.js`：
    `95186d1925bb27db22518babfee9e234d316996b2e2be6279a75568ab4963592`

## 边界与下一动作

- 仅修改只读前端 Checklist 与静态合同；未启动 8911/5174、API、provider、浏览器或真实项目，未
  读写权威 SQLite，未触碰 18911/PID 43191、医学写作或其他并行模块。
- B6 仍为 `pending_review`（5 candidates/0 outcomes/2 blockers），C13 仍 blocked；本切片不解锁
  reviewer outcome、source lineage revalidation、aggregate/CAS、迁移、事件创建、投影激活或商业
  发布。
- 下一安全动作仍是取得 hash-bound 授权 reviewer outcome，随后按顺序完成 aggregate/source-token
  replay 与 approved-input 内存 dry-run；在此之前继续只做离线合同/只读 UI 防护。
