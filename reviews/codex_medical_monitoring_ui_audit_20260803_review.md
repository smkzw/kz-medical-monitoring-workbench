# Codex 审查：medical_monitoring_ui_audit_20260803

日期：2026-08-03

## 结论

本轮限定 UI 审查与项目服务边界修订通过；真实医学监查业务链路仍因 8911 按约停止而未验收。

## 证据与验证

- 真实 Vite preview 视口 1280×720；DOM snapshots 覆盖初始加载、settled empty state、建项对话框、修订后失败态。
- 重新打开 `02-dashboard-viewport.png`、`03-dashboard-empty-settled.png`、`04-new-project-dialog.png`、`05-project-service-unavailable.png`。
- Vite build 1927 modules 通过；仅有既有大 chunk advisory。
- 修订后：服务失败显示“项目服务暂不可用/项目列表读取失败”；GET-only “重新读取”可见；“新建项目”和模块入口按边界禁用。
- 无浏览器 console error/warn；8911/5174 保持停止。

## 残余风险

真实项目、监查 checklist、风险趋势、subject timeline、Patient Profile、身份授权负向路径、双角色 Playwright/scientific/UAT 和商业化证据仍未完成。
