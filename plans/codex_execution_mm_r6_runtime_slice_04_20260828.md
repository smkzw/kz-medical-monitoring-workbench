# Codex Execution Plan: mm_r6_runtime_slice_04_20260828

Objective: 按 context/medical_monitoring_r6_runtime_slice_04_contract_20260828.md 实现 synthetic/offline 三模式 ModeContract、daily ModeOutput 与结构化 Query 草稿，严格限制允许路径，保护既有 slices 与医学写作，保持 8911/5174 停止。

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | 实现三模式合同与 Run 门：不可变 ModeContract、execution basis、entry conditions、cutoff/source revision、carry-forward、fixed-total 与 silent conversion 失败关闭。 | `runs/execution/mm_r6_runtime_slice_04_20260828/worker_01.md` |
| `worker_02` | 实现通用 ModeOutput 和 daily 四输出，重点结构化 affected Query draft 的依据+发现+行动项、中文确定性投影、证据/身份绑定与未发送未关闭边界。 | `runs/execution/mm_r6_runtime_slice_04_20260828/worker_02.md` |
| `worker_03` | 独立验证模式/输出/Query/tamper/identity/cutoff/producer/authority/数字一致性，跑 normal/-O/-OO×3 hash seeds、全 POC、医学写作边界和端口停止，生成 receipt。 | `runs/execution/mm_r6_runtime_slice_04_20260828/worker_03.md` |

## Manager

No execution manager is dispatched for this route; Codex reviews the worker outputs directly.

## Codex Acceptance

TODO: verify artifacts, tests, source claims, rendered surfaces, blockers, and user-facing completeness.
