# 08C-3 独立代码复核 Round 3 请求

继续同一 `general_single_object` session，只读复核当前磁盘；不得重启任务或复述旧快照。

请重新读取：

- `frontend/src/features/medical-monitoring/r7/MedicalMonitoringR7ProductLoop.jsx` 中 `selectResultEvent` 与 `selectResultContinuityRow`
- `frontend/src/features/medical-monitoring/r5/MedicalMonitoringR5Page.jsx` 中 `selectedJourneyRowRef`、`selectWorkspaceRisk`、`selectWorkspaceEvent` 与 drawer rows 选择
- `frontend/src/features/medical-monitoring/r7/medicalMonitoringR7JourneyDrawerRender.test.mjs` 最后的 integration source contract

Codex 已关闭 Round 2 的唯一 P2：

1. 直接事件选择现在显式写入 `risk_instance_ref: ""`，因此事件入口不会继承陈旧风险上下文，也不会错误进入 risk 聚合行集。
2. 直接风险/事件/视图点击现在都通过 `selectWorkspaceRisk/selectWorkspaceEvent` 清空本地 `selectedJourneyRowRef`；只有抽屉行切换保留精确行 ref。
3. 新增源码契约断言钉死上述两点。
4. 修订后 Codex 再次复跑：R5/R7 23/23、医学监查全量 61/61、Vite build 1981 modules，全部通过。

请确认 Round 1/2 的全部 P0-P2 是否已关闭，且当前修订未引入新的 P0-P2。若已关闭，请明确输出 `ACCEPT` 并注明仅接受 synthetic/offline 08C-3；P3/P4 与视觉、真实 DOM 焦点、三视口及 ego(lite) 均留 08C-4，不得因此阻断本轮接受。
