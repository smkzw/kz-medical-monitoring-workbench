# Codex Execution Plan: mm_r7_slice09b_implementation_20260830

Objective: 按冻结的 R7 Slice-09B v0.1+v0.2 合同实施 synthetic/offline 项目格式只读识别、staging-only 升级、失败恢复和中文产品投影；保护医学写作与真实项目，保持 8911/5174 停止。

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | 实现显式 schema manifest、只读 ProjectSchemaInspector、旧/当前/未知/损坏分类和 synthetic legacy fixture/单元测试；普通 constructor 对 legacy/unknown/malformed fail closed 且零字节改动。 | `runs/execution/mm_r7_slice09b_implementation_20260830/worker_01.md` |
| `worker_02` | 实现 migration plan、根级 ledger 扩展、sibling staging、R1 4/5到6 与 launch v1/v2/v3到v4 的 marker-last staged migration、目录切换/回滚、崩溃恢复与故障注入测试，复用 09A 维护门/指纹/闭包原语。 | `runs/execution/mm_r7_slice09b_implementation_20260830/worker_02.md` |
| `worker_03` | 实现最小中文 ProjectOpen/Upgrade progress/result DTO 与产品路由、legacy 持久化只读 facade/写阻断，并建立 DTO 禁用字段、确定性、09A/R1/R7 相邻回归和边界证据。 | `runs/execution/mm_r7_slice09b_implementation_20260830/worker_03.md` |

## Manager

No execution manager is dispatched for this route; Codex reviews the worker outputs directly.

## Codex Acceptance

TODO: verify artifacts, tests, source claims, rendered surfaces, blockers, and user-facing completeness.
