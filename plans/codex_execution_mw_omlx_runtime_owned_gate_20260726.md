# Codex Execution Plan: mw_omlx_runtime_owned_gate_20260726

Objective: 让oMLX共享gate成为OCR与翻译模型选择和并发准入的唯一权威，产品消费lease模型并阻止任何绕过或人工覆盖，同时保持8/8/16合同和现有专用链路

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | global gate: selection/config contract, caller override fail-closed, deterministic tests | `runs/execution/mw_omlx_runtime_owned_gate_20260726/worker_01.md` |
| `worker_02` | product client and role runtime: consume the gate-owned model, remove manual OCR/body-model choice, migrate runtime projection and tests | `runs/execution/mw_omlx_runtime_owned_gate_20260726/worker_02.md` |
| `worker_03` | oMLX transport boundary: enforce one shared lease without double acquisition, add product-combination concurrency and failure-path regression tests | `runs/execution/mw_omlx_runtime_owned_gate_20260726/worker_03.md` |

## Manager

| Role | Provider | Model | Report |
|---|---|---|---|
| `finite_code_manager_cursor` | `cursor-cli` | `auto` | `runs/execution/mw_omlx_runtime_owned_gate_20260726/manager.md` |

## Codex Acceptance

TODO: verify artifacts, tests, source claims, rendered surfaces, blockers, and user-facing completeness.
