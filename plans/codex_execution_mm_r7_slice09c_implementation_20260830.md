# Codex Execution Plan: mm_r7_slice09c_implementation_20260830

Objective: 按冻结合同 v0.2 实施 R7 Slice-09C synthetic/offline 项目级业务审计核验、09A/09B 恢复边界接线与 bounded technical logs；完成聚焦、故障注入、确定性和相邻回归，保持 8911/5174/8984 停止，不运行真实项目/模型/浏览器，不触碰医学写作、安全专项、视觉或09D性能。

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | 实现根级 ProjectAuditLedger：schema、每项目 CAS chain head、per-kind allowlist、canonical hashing、根级 operation 投影同事务 API、链验证/篡改检测与完整 synthetic tests；只改 R7 项目审计模块、必要根账本 schema/公共导出及其测试，不改技术日志或产品路由。 | `runs/execution/mm_r7_slice09c_implementation_20260830/worker_01.md` |
| `worker_02` | 实现冻结合同的 stdlib bounded technical log：固定九字段 JSONL、1MiB+4 archive、7天、8KiB、0600、realpath/unknown/symlink保护、非阻塞跨进程锁和有界 degraded；只改独立日志模块/公共导出及其 focused tests，不触碰 execution/conference/runs 证据。 | `runs/execution/mm_r7_slice09c_implementation_20260830/worker_02.md` |
| `worker_03` | 实现 09C ProjectVerifier 与最小中文 DTO，并接入 09A/09B boundary/recovery/rollback 及 startup/open/same-key 统一协调路径；直接复用 R1 公共 verify_audit_chain，核对 publication/continuity 只读锚点；补齐产品路由和 focused/integration/fault/determinism tests，避免重写前两项模块，不新增 UI。 | `runs/execution/mm_r7_slice09c_implementation_20260830/worker_03.md` |

## Manager

No execution manager is dispatched for this route; Codex reviews the worker outputs directly.

## Codex Acceptance

TODO: verify artifacts, tests, source claims, rendered surfaces, blockers, and user-facing completeness.
