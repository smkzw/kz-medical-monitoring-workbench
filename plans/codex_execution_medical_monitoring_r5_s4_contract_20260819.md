# Codex Execution Plan: medical_monitoring_r5_s4_contract_20260819

Objective: 实施并独立冻结R5-S4 Risk Inspector synthetic/offline renderer-neutral精确合同；不得实现runtime/UI

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | worker_01: 编写human contract、exact schema/enums/mappings/join/invariants/source pins | `runs/execution/medical_monitoring_r5_s4_contract_20260819/worker_01.md` |
| `worker_02` | worker_02: 实现deterministic generator/verifier/manifest与normal+O2 tamper gates | `runs/execution/medical_monitoring_r5_s4_contract_20260819/worker_02.md` |
| `worker_03` | worker_03: 实现非self-proof challenge registry/tests并做独立预审交接 | `runs/execution/medical_monitoring_r5_s4_contract_20260819/worker_03.md` |

## Manager

No execution manager is dispatched for this route; Codex reviews the worker outputs directly.

## Codex Acceptance

Workers sequentially consume the prior accepted work item; no parallel writes.

- W1: human contract plus deterministic source-of-truth generator and initial exact artifacts.
- W2: independent verifier, hard pins/exact artifact set, normal/O2 and tamper closure; may repair W1 only within the S4 write set.
- W3: non-self-proof challenge fixtures/tests, boundary regression and immutable-SHA handoff; may repair remaining S4-only gaps.
- Codex then runs generator/check/verifier/tests/Ruff/compile/SHA/8911 gates and sends the stable snapshot to a fresh isolated reviewer.
- Any P0–P4 or file drift returns to the same relevant worker/reviewer session; runtime remains locked until `ACCEPT_R5_S4_CONTRACT`.

## Completion

`ACCEPT_R5_S4_CONTRACT`。W1→W2→W3 与同一 fresh reviewer 的多轮闭环已完成。
本接受仅解锁 S4 runtime 精确薄切合同；不解锁 UI/S7/8911、真实项目、
真实模型、医学写作或生产。详见
`context/medical_monitoring_r5_s4_contract_acceptance_record_20260819.md`。
