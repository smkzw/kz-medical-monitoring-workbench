# Codex Execution Plan: mm_r7_slice08b_contract_20260829

Objective: 冻结R7 Slice-08B真实R5 authority、R6 ModeOutput子项与publication artifact成员/字节校验的最窄实现合同；不得修改产品源码、启动服务或真实项目

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | 核对现有R5PublicationAuthorityInputAssembler/R5AuthorityPacket的身份、摘要、成员和项目运行边界，提出只复用不重建的桥接合同 | `runs/execution/mm_r7_slice08b_contract_20260829/worker_01.md` |
| `worker_02` | 核对R6 ModeOutput三模式结构、validate_mode_output与可独立沿用子项，定义canonical子项摘要、禁止整包/页面沿用与失败关闭条件 | `runs/execution/mm_r7_slice08b_contract_20260829/worker_02.md` |
| `worker_03` | 核对R7 ResultPublication/continuity registry现有schema，定义最小additive artifact member清单、授权根路径下真实字节SHA-256复核、CAS/重放/迁移测试矩阵及08B非目标 | `runs/execution/mm_r7_slice08b_contract_20260829/worker_03.md` |

## Manager

No execution manager is dispatched for this route; Codex reviews the worker outputs directly.

## Codex Acceptance

TODO: verify artifacts, tests, source claims, rendered surfaces, blockers, and user-facing completeness.
