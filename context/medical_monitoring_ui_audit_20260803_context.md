# 医学监查工作台 UI 审查上下文（2026-08-03）

## 目标与边界

从资深医学监察员的实际视角检查当前渲染入口，保持 8911/5174 停止，不伪造项目、不登录 API、不触碰 B6/C14、后端权限、真实项目数据或医学写作源文件。允许在证据充分且可回滚的前端边界做最小修订。

## 当前证据

- 安全预览：`http://127.0.0.1:4173/`。
- 浏览器：Codex in-app browser Playwright 子集；截图与 DOM 证据在 `evidence/medical_monitoring_ui_audit_20260803/`。
- 8911/5174：停止；因此没有真实项目监查、风险 checklist、subject timeline/profile 或科学核查证据。
- 原问题：`/api/projects` 失败被渲染为“暂无项目”，同时仍提供“新建项目”。

## 已完成

- `frontend/src/App.jsx` 增加 `projectsLoadError`、GET 重试 nonce、明确服务不可用提示。
- 服务加载中或失败时，顶栏新建项目禁用；失败态显示“重新读取”；无活动项目时医学监查等模块继续禁用。
- `npm run build` 通过；浏览器 reload 后 DOM/screenshot 复核通过；console error/warn 为空。
- `styles.css` 未修改。App 当前 SHA-256：`d746bdfee64bc6641bfc3ae5f01602335f90d6db1856a3f3549ebb4119e124b7`。

## 后续安全顺序

正式 B6 reviewer outcome → 重开哈希 → aggregate/CAS 与 legacy source-token → approved-input → controlled runtime identity → 真实项目 Playwright/scientific/UAT LOOP。不得把当前空态审查当作业务或商业验收。
