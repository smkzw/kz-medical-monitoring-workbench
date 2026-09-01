# Codex Execution Plan: mm_r7_slice08c3_implementation_20260830

Objective: 实现R7 Slice-08C-3 synthetic/offline Patient Journey本轮变化标记、同身份详情抽屉及subject-view continuity读取；完成离线交互/可访问性/相邻回归，不启动服务浏览器真实项目或模型

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | 实现纯函数 continuity-to-Journey 同身份同窗筛选、event/risk绑定、七类变化显示模型与路由关闭补丁，并补聚焦测试 | `runs/execution/mm_r7_slice08c3_implementation_20260830/worker_01.md` |
| `worker_02` | 在现有R5横向访视轴上接入R7-only变化标记和右侧overlay/push详情抽屉，保持legacy R5与既有八域几何不变，补渲染/键盘/焦点/阈值测试 | `runs/execution/mm_r7_slice08c3_implementation_20260830/worker_02.md` |
| `worker_03` | 在R7 ProductLoop为journey/profile/timeline接入可取消continuity读取、stale清空、route驱动开关及集成回归，补全全部R7/R5相邻测试和Vite build | `runs/execution/mm_r7_slice08c3_implementation_20260830/worker_03.md` |

## Manager

No execution manager is dispatched for this route; Codex reviews the worker outputs directly.

## Codex Acceptance

- worker_01：纯函数与边界测试通过；不触碰 UI、ProductLoop 或医学写作。
- worker_02：R7-only 变化标记/抽屉与 legacy R5 边界有结构化断言；不启动浏览器。
- worker_03：subject-view continuity 读取、取消/清空/route 集成通过；全 R7、相邻 R5、Vite build 通过。
- Codex 在合并后的当前树复查全部变更，修复 worker 之间的集成冲突，复跑决定性测试并检查 8911/5174 停止。
- 独立代码会商关闭 P0–P2 后才接受实现；视觉与 ego(lite) 仍留 08C-4。
