# Codex Execution Plan: mm_r7_slice07c2_prepare_start_implementation_20260829

Objective: 实现冻结的 R7 Slice-07C-2 synthetic/offline 原子 prepare-and-start、public run history、幂等与长等待恢复；不实现发布、result-entry、前端或真实项目。

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | 新增 stdlib-only launch registry：项目级 SQLite busy_timeout/显式关闭、规范请求指纹、public token、同 key 重放/冲突、状态与有界历史；只改 R7 POC 新模块及必要导出。 | `runs/execution/mm_r7_slice07c2_prepare_start_implementation_20260829/worker_01.md` |
| `worker_02` | 在产品 R7 router 接入 POST /runs/prepare-and-start 与 GET /runs：服务端解析 snapshot/baseline/rule tokens，生成 manifest，绑定、准备、启动并公开中文历史；只改 router 与产品路由测试。 | `runs/execution/mm_r7_slice07c2_prepare_start_implementation_20260829/worker_02.md` |
| `worker_03` | 补充 synthetic 多候选锁库前 baseline、三模式/幂等/跨项目/过期 token/start 失败恢复/确定性测试、evidence receipt 与 README；只改 R7 tests/evidence/README，不改产品源码。 | `runs/execution/mm_r7_slice07c2_prepare_start_implementation_20260829/worker_03.md` |

## Manager

No execution manager is dispatched for this route; Codex reviews the worker outputs directly.

## Codex Acceptance

Accepted as `ACCEPT_R7_SLICE_07C2_SYNTHETIC_LIMITED` on 2026-08-29 after Codex
source review, `43 passed` product-router tests, `181 passed` full R7 tests,
compileall, stopped-port checks, execution audit, and a three-pass same-session
DeepSeek V4 Flash max conference ending in `ACCEPT`. Codex corrected stale
history state, reservation-only retry recovery, per-record history isolation,
cross-project token and role coverage before acceptance. No visual surface was
introduced in this slice; browser acceptance is deferred to the frontend slice.
