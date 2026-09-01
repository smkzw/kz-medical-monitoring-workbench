# 医学监查独立 AI 规则建议形状防护（LOOP 3.81）

**时间：** 2026-08-02 07:45 CST  
**范围：** 前端“已确认方案事实 → 独立 AI 规则建议 → 医学经理采用/驳回”响应消费；不启动服务、不调用 API/provider、不触发 AI 任务、不打开浏览器、不运行真实项目、不写权威运行库。

## 结论

规则建议面板原先把独立 AI 的状态、候选、映射字段和采用回执交给宽松的 `|| []`/默认对象处理。若候选身份、方案来源、字段映射、输入 revision 或决策回执形状错误，界面可能继续展示候选、保留旧候选，或把异常响应带入医学采用路径。

本 LOOP 新增 `frontend/src/features/medical-monitoring/medicalMonitoringRuleTemplateView.mjs`，并让方案准备面板统一校验：

- 状态/启动回执：项目、方案事实、事实 state version、方案来源定位、字段映射 revision/activation disposition、64 位 input revision、状态与 failure/message；
- 候选：candidate id/status、标题/摘要/理由、tradeoffs、required domains、mapping fields 的 domain/field/role、方案原文与定位；候选身份重复或数组/scalar 形状异常即拒绝；
- 采用/驳回回执：闭合状态、候选身份一致性、`decision_reused` 布尔值、confirmed fact、compiled rule 与下一步 code；不允许把未知下一步当成规则包发布；
- 形状异常时清空当前规则建议 payload，避免旧候选继续显示或继续提交；不改变独立 AI 的生成、路由、重试或医学经理最终采用权。

后端公开状态中的事实对象不重复传 `project_id`，决策候选也不重复传项目字段；守卫以已验证的顶层项目上下文补足这些裁剪字段，不从缺失字段推断医学内容。候选仍必须携带真实方案原文与 locator，状态仍保持“待用户确认/已处理”语义。

## 验证

- `node frontend/src/features/medical-monitoring/medicalMonitoringRuleTemplateView.test.mjs`：**13 passed**；覆盖合法 status/候选/采用/驳回、跨项目、scalar 候选、字段映射、摘要、重复身份、错误下一步和 decision CAS 形状；
- `node frontend/src/features/medical-monitoring/medicalMonitoringRuleTemplateRecommendation.test.mjs`：**22 passed**；
- `node frontend/src/features/medical-monitoring/medicalMonitoringProjectSwitchIsolation.test.mjs`：**52 passed**；
- 全部 `frontend/src/features/medical-monitoring/*.test.mjs`：**21 个文件全部通过**；
- `python3 -m pytest -q tests/test_frontend_monitoring_contract.py tests/test_frontend_unified_risk_workbench_contract.py tests/test_frontend_timeline_contract.py`：**54 passed**；
- `npm run build`（工作目录 `frontend/`）：Vite **1924 modules transformed**，构建成功；仅保留既有大 bundle warning。

本次关键 SHA-256：

- `frontend/src/features/medical-monitoring/medicalMonitoringRuleTemplateView.mjs`：`474ab05e79e9ce4bd57b0c9edb00b6eb1086f188caea79fc84df562d801cba5b`；
- `frontend/src/features/medical-monitoring/medicalMonitoringRuleTemplateView.test.mjs`：`c279d4eb6d450847797bf50dd6f753db35575251b99788fee02b34ec5e31b76c`；
- `frontend/src/features/medical-monitoring/MedicalMonitoringProtocolPreparationPanel.jsx`：`145ffe812f9c2e3cd34083762c46ebea9875c3b40f9b739121536adfe8d65ed1`；
- `frontend/src/features/medical-monitoring/medicalMonitoringProjectSwitchIsolation.test.mjs`：`0ce53ce9583347edb9ea8dff3d84e2e63533628cc8dd2332cbd6c96a02e42e0e`；
- `frontend/dist/assets/index-Clo4TtJR.js`：`fa43fa5cde98ad8b4f47c23a3ca9d57259a14cf1c6cadff3a024c377944fc163`；
- `frontend/dist/index.html`：`17db7c2e8afca6582db77946ac72aebdc0e52c58ea797067cff89c2a0f3ff347`；
- `frontend/dist/runtime-build.json`：`d6ed45bdf3823f278e0c1b30ff1e7b1bc3639d2e8ba71e9c4e2b6dc6ee805021`。

## 边界与未证明项

这是独立 AI 规则建议 UI 的输入形状/项目隔离/候选证据显示安全合同，不是 AI 语义正确性、四类任务 × 三项目独立评估、超时/低置信度/无效 JSON/重启恢复、真实方案/listing、医学采用科学性、B6 authority、aggregate/CAS、真实 runtime、浏览器视觉验收或商业上线证据。B6 仍 `pending_review`（5 candidates、0 outcomes、`migration_ready=false`、`write_permitted=false`）；C13 仍 3 个 schema-only reports 且 `activation_allowed=false`；8911/5174 必须继续停止。

下一安全动作仍是：授权 B6 reviewer outcome → 实际 aggregate snapshot/CAS replay 与 MY009 source-token revalidation → approved-input 内存 dry-run；之后才能重新申请受控 runtime、独立 AI 评估、三项目真实批次 LOOP 与浏览器/科学性验收。

