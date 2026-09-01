# Codex Execution Plan: mm_r8_gate2_synthetic_runtime_20260831

Objective: 在不访问真实项目、不调用模型、不启动服务或浏览器、不修改医学写作子系统的前提下，实现并验证 R8 G2 synthetic runtime：canonical digest/manifest revision replay、macOS synthetic source_access_profile、以及不占真实端口的一键 start-stop-restart 生命周期演练。

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | 设计并实现纯标准库 canonical digest 规范表、synthetic source/output manifest schema、revision chain 与独立 replay；只修改医学监查 deploy 新模块及其专门测试。 | `runs/execution/mm_r8_gate2_synthetic_runtime_20260831/worker_01.md` |
| `worker_02` | 设计并实现目标 macOS synthetic shadow-root source_access_profile 证据：读取允许、写入拒绝、写事件可观察、监测失效 not_evaluable；不得对真实来源做写探针。 | `runs/execution/mm_r8_gate2_synthetic_runtime_20260831/worker_02.md` |
| `worker_03` | 设计并实现 synthetic/offline one-click 生命周期演练：start-stop-restart/ready/failure/partial/foreign ownership 均由合成 adapter 驱动且绝不绑定 8911/5174/8984；补中文文档与测试。 | `runs/execution/mm_r8_gate2_synthetic_runtime_20260831/worker_03.md` |

## Manager

No execution manager is dispatched for this route; Codex reviews the worker outputs directly.

## Codex Acceptance

TODO: verify artifacts, tests, source claims, rendered surfaces, blockers, and user-facing completeness.
