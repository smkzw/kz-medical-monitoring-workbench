# Codex Execution Plan: mm_r7_slice08c4_visual_execution_20260830

Objective: 在冻结08C-4合同下实现专用synthetic fixture，并用ego(lite)完成1280/1440/1920真实运行时视觉基线、专项美化、结构化对账与清理；保护医学写作和8911/5174，不运行真实项目或模型，全部P0-P4清零后才进入独立视觉会商

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | 已完成：实现并静态校验08C-4专用synthetic fixture、continuity公开路由、三种result_context与七状态证据；未启动受保护端口/真实项目/模型 | `runs/execution/mm_r7_slice08c4_visual_execution_20260830/worker_01.md` |
| `worker_02` | 已完成：ego(lite) 三视口基线、键盘/焦点、overlay/push、数据对账与 71+ 文件证据；记录 D1-D6，保留 8984/task-space 供修复轮 | `runs/execution/mm_r7_slice08c4_visual_execution_20260830/worker_02.md` |
| `worker_03` | 已完成：按参考+基线修复 D1-D6，ego(lite) 三视口重捕获与并列图完成，结构化 `p0_to_p4_clear=true`；保留运行时给最终验证 | `runs/execution/mm_r7_slice08c4_visual_execution_20260830/worker_03.md` |
| `worker_04` | 已完成：23/23 聚焦、61/61 全量、Vite build、医学写作保护、端口/ego 清理与视觉会商输入包 | `runs/execution/mm_r7_slice08c4_visual_execution_20260830/worker_04.md` |

## Manager

No execution manager is dispatched for this route; Codex reviews the worker outputs directly.

## Codex Acceptance

Codex 已打开参考+baseline+revised 并列图及 1280/1440/1920 原图，发现并追加关闭 1280 `检查依据` 卡片重叠 P2；worker_03 同会话补测、重建、清理并补齐 1920 push collage。执行接受仍以独立 visual conference 为最终主观验收门。
