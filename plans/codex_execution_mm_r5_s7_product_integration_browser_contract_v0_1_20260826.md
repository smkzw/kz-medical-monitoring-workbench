# Codex Execution Plan: mm_r5_s7_product_integration_browser_contract_v0_1_20260826

Objective: 冻结R5-S7产品最小接入与真实浏览器验收合同：精确限定前后端allowlist、医学写作保护、8911临时生命周期、中文用户语义、Playwright多视口/性能/交互/console-network证据、用户指定视觉模型后续角色及关闭条件；本阶段不改产品源码、不启动服务。

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | 合同架构：读取R5 v0.3、S5/S6 accepted evidence、现有产品医学监查入口，产出精确product allowlist、只读API/adapter边界、迁移/回滚/身份/医学写作保护合同。 | `runs/execution/mm_r5_s7_product_integration_browser_contract_v0_1_20260826/worker_01.md` |
| `worker_02` | 浏览器与产品体验合同：冻结中文原生信息架构、Patient Journey共享访视轴、八域事件和风险编码、桌面任务/点击/时长/可访问性/高密度/性能、Playwright截图与console/network证据矩阵。 | `runs/execution/mm_r5_s7_product_integration_browser_contract_v0_1_20260826/worker_02.md` |
| `worker_03` | 独立验证：机械核验合同闭合、路径与哈希、8911停止、禁止越界、后续视觉execution与独立visual conference分离，输出唯一ACCEPT或REVISE裁决。 | `runs/execution/mm_r5_s7_product_integration_browser_contract_v0_1_20260826/worker_03.md` |

## Manager

No execution manager is dispatched for this route; Codex reviews the worker outputs directly.

## Codex Acceptance

1. Dispatch workers 01 and 02 using the generated commands and wait for terminal completion.
2. Codex reads both outputs, assembles one exact contract plus one machine-readable matrix, records current hashes/inventories and keeps 8911 stopped.
3. Dispatch worker 03 in its original session against the assembled artifacts; any `REVISE` is corrected and rechecked in the same session.
4. Codex mechanically validates JSON, exact paths/hashes, protected medical-writing inventory and stopped ports, then records contract acceptance.
5. Only an accepted S7 contract unlocks a separate product implementation execution. Browser/visual execution and visual/medical conference remain later, separate governed packets.
