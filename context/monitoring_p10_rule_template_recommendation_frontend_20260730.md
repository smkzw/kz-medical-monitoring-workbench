# 医学监查规则模板建议前端闭环交接

## 范围

- 实现链路：已接受方案事实草稿 -> 独立 AI 规则模板建议 -> 用户选择即确定性编译。
- 产品代码仅修改 `frontend/src/features/medical-monitoring/`。
- 未修改后端、医学写作文件或运行数据库。

## 已实现

1. 从刷新状态中的 `candidate.fact` 恢复 `fact_revision_id` 与 `state_version`；从本次接受响应的 `outcome.fact` 或 `candidate.fact` 恢复新事实。
2. 仅在本次用户接受方案候选成功后自动调用规则建议 `start`；刷新恢复仅 GET 当前状态，`ready` 时只显示一个“生成规则建议”按钮。
3. `queued/running` 使用紧凑进度；不支持确定性规则的事实显示简短人工处理说明。
4. 候选审核最多展示 3 条，包含标题、摘要、推荐理由、取舍、所需数据域/字段和方案原文；源内容优先、定位次要。
5. “采用”在同一请求中完成用户决定与确定性编译；成功后明确尚未进入规则包、影子验证或发布。
6. 决定请求同时携带 `expected_input_revision_sha256` 与事实 `state_version`；错误不自动密集重试。
7. 页面不展示 provider、model、job_id、prompt、hash 等运行日志，不引入第二次医学批准。

## 改动文件

- `frontend/src/features/medical-monitoring/MedicalMonitoringProtocolPreparationPanel.jsx`
- `frontend/src/features/medical-monitoring/MedicalMonitoringProtocolPreparationPanel.css`
- `frontend/src/features/medical-monitoring/medicalMonitoringProtocolPreparation.mjs`
- `frontend/src/features/medical-monitoring/medicalMonitoringRuleTemplateRecommendation.mjs`
- `frontend/src/features/medical-monitoring/medicalMonitoringRuleTemplateRecommendation.test.mjs`
- `frontend/src/features/medical-monitoring/medicalMonitoringApi.mjs`
- `frontend/src/features/medical-monitoring/medicalMonitoringApi.test.mjs`

## 验证

- `node medicalMonitoringRuleTemplateRecommendation.test.mjs`：通过。
- `node medicalMonitoringProtocolPreparation.test.mjs`：通过。
- `node medicalMonitoringApi.test.mjs`：通过。
- 医学监查目录全部 Node 状态测试：通过。
- `npm run build`：Vite 生产构建通过，1908 个模块完成转换。

## 残余风险

- 2026-07-30 本轮核对时，`127.0.0.1:8911` 当前运行实例的 OpenAPI 尚未暴露 `rule-template-recommendations` 三个端点，因此未在真实 API 上完成浏览器点击闭环。前端已严格按当前 router/service 公开合同实现；后端路由挂载或服务重启后需补一次真实运行态验收。
- Vite 仍报告既有主 bundle 大于 500 kB；本轮没有在医学监查局部功能中扩大为全局拆包改造。
