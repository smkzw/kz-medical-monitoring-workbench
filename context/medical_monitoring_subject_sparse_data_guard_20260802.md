# 医学监查 Timeline/Profile 稀疏数据防御记录

**日期：** 2026-08-02  
**范围：** 纯前端模型函数与 Node 回归；不启动服务、不调用 API/provider、不接真实项目。

## 发现

`referenceRiskCards()` 在 CM 事件存在但缺少 `title` 或 `detail` 时直接调用字符串
`.replace()`，稀疏 listing、字段缺失或后端受限投影会导致风险卡渲染异常。该边界与
`clinical-patient-profile-html` 的来源保留/缺失提示要求以及 `subject-timeline-builder`
的“不确定字段不得静默推断”原则一致，需要 fail-safe 展示而不是崩溃或补造事实。

## 修复

- `cmTitle`、`cmDetail`、`cmDate` 统一转为有界的显示占位：`CM事件`、`用药详情未提供`、
  `日期未提供`；不改变原始事件、不生成医学判断。
- 新增 sparse CM fixture，断言 `referenceRiskCards()` 不抛异常并保留可读风险标题。
- 修改文件：
  - `frontend/src/features/medical-monitoring/medicalMonitoringSubjectModels.mjs`
  - `frontend/src/features/medical-monitoring/medicalMonitoringSubjectModels.test.mjs`

## 验证

- 聚焦：`node frontend/src/features/medical-monitoring/medicalMonitoringSubjectModels.test.mjs`
  → passed。
- 医学监查前端全部 16 个 `*.test.mjs` → 全部 passed：共覆盖现有 API、assurance、rollup、
  checklist、consumer、daily-run gate、mapping、model、project scope/switch、protocol、
  risk projection、route、rule release/template、subject model 套件；本批次无失败。
- 源文件 SHA-256：
  - model：`a25860220b8802b25476decc8bb119280aff0a3e5aabe47cd7d8856254a8b758`
  - test：`4c13fb247ec303034d1dbd2fc1ea04a6e2b4224ba8a13548a07117a838625b3a`

## 未覆盖

未执行 Vite/browser rendering、窄视口、真实三项目数据、Timeline/Profile source locator 逐项
验收、B6 authority、runtime/persistence 或总系统写作消费者回归；这些仍按 P0–P10 release-gate
总账保持未证明/阻断。
