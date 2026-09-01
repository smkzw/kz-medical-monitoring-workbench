# Codex Execution Plan: mw_assembly_plan_consumers_20260722

Objective: 将ProtocolAssemblyPlan真正接入医学写作所有下游消费者，并关闭I期typed Parts和AI失败时确定性临床设计候选问题

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | Typed Phase I parts and safe AI-first prefill | `runs/execution/mw_assembly_plan_consumers_20260722/worker_01.md` |
| `worker_02` | Synopsis chapter SoA flowchart DOCX projection consumption | `runs/execution/mw_assembly_plan_consumers_20260722/worker_02.md` |
| `worker_03` | Evidence corpus and AI candidate projection consumption | `runs/execution/mw_assembly_plan_consumers_20260722/worker_03.md` |

## Manager

| Role | Provider | Model | Report |
|---|---|---|---|
| `complex_manager_grok` | `grok-build` | `grok-4.5` | `runs/execution/mw_assembly_plan_consumers_20260722/manager.md` |

## Codex Acceptance

1. Manager planning pass defines exact disjoint write sets and serial order before worker dispatch.
2. Worker output is accepted only after current-source inspection and Codex test reproduction.
3. `rg` must show real consumers outside `main.py`, the plan service and its own tests.
4. Cross-projection counterexamples must fail before repair and pass after repair.
5. Browser and Word acceptance remain Codex-owned later E4/E5 gates; this execution closes backend E2/E3
   contracts only unless real runtime evidence is explicitly produced.
