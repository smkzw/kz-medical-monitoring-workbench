# 08C-3 独立代码复核 Round 2 请求

继续同一 `general_single_object` session；不得重启任务、不得沿用上一轮缓存的源码内容。请重新读取当前磁盘中的：

- `frontend/src/features/medical-monitoring/r7/MedicalMonitoringR7ProductLoop.jsx`
- `frontend/src/features/medical-monitoring/r5/MedicalMonitoringR5Page.jsx`
- `frontend/src/features/medical-monitoring/r7/medicalMonitoringR7JourneyDrawerRender.test.mjs`
- `reviews/codex_execution_mm_r7_slice08c3_implementation_20260830_review.md`
- `metrics/mm_r7_slice08c3_implementation_20260830_execution_metrics.md`

Codex 已针对上一轮两项 P2 与相邻 P3 做了以下修订：

1. 从 subject result 读取 effect 的依赖中移除 `event_ref/risk_anchor_ref/risk_instance_ref/visit_ref`，行切换不再清空并重挂整个受试者工作区。
2. `SubjectWorkspaceView` 使用本地 `selectedJourneyRowRef` 精确保持当前变化行；切换行仍将公共路由选择键镜像更新。
3. risk 上下文优先使用 `selectedRiskRows` 全量聚合，不再被 event 行集截断；纯 event 上下文仍使用 `selectedEventRows`。
4. 行切换 patch 总是替换并在缺值时清空 `risk_instance_ref/risk_anchor_ref/event_ref/visit_ref`，避免陈旧选择键。
5. Codex 已复跑：R5/R7 23/23 test files、医学监查全量 61/61 test files、Vite build（1981 modules）均通过。

请对当前源码逐项验证这些修订是否真正关闭 P2-1/P2-2；同时检查是否引入新的 P0-P2。若所有 P0-P2 已关闭，明确输出 `ACCEPT`；否则输出 `REVISE` 并给出精确源码证据。视觉、真实 DOM 焦点和 ego(lite) 仍属于 08C-4，不得因未执行而阻断本次 synthetic/offline 代码接受。
