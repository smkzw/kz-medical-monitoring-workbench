# Codex Execution Plan: mm_r5_s7_product_integration_runtime_v0_1_20260826

Objective: 按已接受的R5-S7合同与闭合allowlist实现产品最小接入：新增GET-only R5后端router/adapter与前端R5页面/adapter/route/CSS/fixtures，做最小App/main/read-action接线，完成聚焦和相邻离线回归及production build；本execution不启动8911/5174/浏览器，不运行真实项目/模型，不修改医学写作。

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | 后端实现：仅写合同4.2/4.3精确allowlist，提供三条GET-only R5 API、synthetic隔离projection、完整identity/digest/read-only envelope、fail-closed参数与测试；最小修改main.py/read-action contract。 | `runs/execution/mm_r5_s7_product_integration_runtime_v0_1_20260826/worker_01.md` |
| `worker_02` | 前端实现：仅写合同4.1精确allowlist，新增中文R5项目/中心/风险/受试者医学旅程页面、八域+风险编码、独立route state与GET-only adapter，并对App.jsx做最小R5 closed-view接线；完成Node合同测试和build。 | `runs/execution/mm_r5_s7_product_integration_runtime_v0_1_20260826/worker_02.md` |
| `worker_03` | 独立验证：后端/前端合并后机械检查exact allowlist、医学写作inventory、8911/5174停止、GET-only/no-fallback、中文禁词、S5/S6 identity、聚焦/相邻测试与production build，输出ACCEPT或REVISE；不得改源码。 | `runs/execution/mm_r5_s7_product_integration_runtime_v0_1_20260826/worker_03.md` |

## Manager

No execution manager is dispatched for this route; Codex reviews the worker outputs directly.

## Codex Acceptance

1. Run worker 01 and worker 02 concurrently because their write sets are disjoint except for separately owned integration seams.
2. Codex reviews exact diffs/hashes, resolves any interaction defect and runs focused backend/frontend tests plus production build.
3. Run worker 03 against the merged current filesystem. Any REVISE is corrected and rechecked in the same session.
4. Record runtime implementation acceptance only if exact allowlist, tests/build, protected inventory and stopped-port gates pass.
5. Browser execution remains a later governed visual packet; 8911 stays stopped throughout this task.
