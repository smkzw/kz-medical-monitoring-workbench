# Codex Execution Plan: mw_design_projection_unification_20260724

Objective: 将动态研究设计收敛为单一权威投影并完成实际输出级回归

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | 设计NormalizedDesignProjection合同、StudyDefinition归一化入口、legacy自由文本回退边界和I期unresolved blocker | `runs/execution/mw_design_projection_unification_20260724/worker_01.md` |
| `worker_02` | 设计并实现转组、交叉、OLE、样本量再估计、适应性设计typed对象及迁移/一致性校验 | `runs/execution/mw_design_projection_unification_20260724/worker_02.md` |
| `worker_03` | 将摘要、正文适用性、SoA、流程图、DOCX消费统一投影并建立多设计实际成品测试矩阵 | `runs/execution/mw_design_projection_unification_20260724/worker_03.md` |

## Manager

| Role | Provider | Model | Report |
|---|---|---|---|
| `complex_manager_grok` | `grok-build` | `grok-4.5` | `runs/execution/mw_design_projection_unification_20260724/manager.md` |

## Required Manager First Pass

Before any worker writes source, refine the three broad items into a sequential
dependency graph with non-overlapping file ownership. Explicitly decide:

1. the normalized projection contract and its migration boundary;
2. which typed complex-design models must land before consumers;
3. how unresolved Phase I and complex designs block affected outputs;
4. how consumer work is split without parallel edits to shared files;
5. which output-level fixtures prove actual scientific consistency;
6. the smallest safe first implementation slice that can be independently
   accepted and merged.

The first pass is plan/review only. Empty worker reports are expected.

## Codex Acceptance

TODO: verify artifacts, tests, source claims, rendered surfaces, blockers, and user-facing completeness.
