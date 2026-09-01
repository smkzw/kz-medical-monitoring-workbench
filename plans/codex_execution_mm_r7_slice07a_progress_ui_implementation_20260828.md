# Codex Execution Plan: mm_r7_slice07a_progress_ui_implementation_20260828

Objective: 按已接受的 Slice-07A v1.1 合同实现真实进度、后台恢复与现有运行管理员动作界面，保持医学监察员只读验收边界；增加稳定 run_state，完成前端接线、测试和后续 ego(lite) 验收准备。不得修改医学写作或权限模型，不得运行真实项目或设计测试安全功能。

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | 后端公开进度：增加稳定 run_state、修订用户中文错误文案并补齐产品路由与运行时测试；只改 R7 运行进度相关文件。 | `runs/execution/mm_r7_slice07a_progress_ui_implementation_20260828/worker_01.md` |
| `worker_02` | 前端数据层：实现 R7 progress/action API client 与纯 projection，覆盖路由 run_ref、错误码空态、迟到响应、禁止词和动作映射测试。 | `runs/execution/mm_r7_slice07a_progress_ui_implementation_20260828/worker_02.md` |
| `worker_03` | 前端呈现层：在现有 R5 页面接入紧凑本次监查进度组件，完成真实轮询、离页恢复、内联停止确认、可访问性、中文视觉与组件测试；不触碰 Patient Journey/Sankey。 | `runs/execution/mm_r7_slice07a_progress_ui_implementation_20260828/worker_03.md` |

## Manager

No execution manager is dispatched for this route; Codex reviews the worker outputs directly.

## Codex Acceptance

- Verify every changed file against the accepted v1.1 contract and current filesystem.
- Run focused backend tests, focused frontend tests, full relevant R7 product-router regression, and Vite build.
- Confirm no medical-writing or authorization-model file changed.
- Confirm 8911 and frontend service stay stopped until code/test acceptance.
- After code acceptance, run a separate isolated ego(lite) visual execution and separate visual conference; do not infer browser acceptance from worker reports.
- Audit execution route identity and archive the packet only after Codex acceptance.
