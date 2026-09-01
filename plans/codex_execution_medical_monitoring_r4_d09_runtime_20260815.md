# Codex Execution Plan: medical_monitoring_r4_d09_runtime_20260815

Objective: 在 R4 POC 内实现并独立验收冻结 D09 v0.5 的 179-case synthetic/offline 中心模式 runtime，保持 8911 停止且保护医学写作及真实项目

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | Worker 01: typed contract, artifact test adapter, deterministic evaluator, exact core/trace/source oracle parity | `runs/execution/medical_monitoring_r4_d09_runtime_20260815/worker_01.md` |
| `worker_02` | Worker 02: renderer-neutral risk, Chinese Query, hotspot, deep-link, visibility, count and R2 handoff projection | `runs/execution/medical_monitoring_r4_d09_runtime_20260815/worker_02.md` |
| `worker_03` | Worker 03: public exports, mutation/anti-overfit/replay/closure suites and focused/adjacent/full regression | `runs/execution/medical_monitoring_r4_d09_runtime_20260815/worker_03.md` |

## Manager

No execution manager is dispatched for this route; Codex reviews the worker outputs directly.

## Codex Acceptance

Workers run strictly serially. Worker 01 owns the typed kernel/evaluator and
test adapter; Worker 02 consumes that frozen interface for renderer-neutral
projection; Worker 03 closes exports, mutation/replay and regressions. Codex
reviews and freezes each item before dispatching the next.

Runtime source may never read/import the catalog, oracle, registry, generators
or acceptance tests, branch on case/fixture/test identifiers or expected
leaves, or interpret free-text/display labels. Only the test adapter may read
the frozen JSON chain. Acceptance requires exact 179/179 oracle parity with no
exceptions; global-vs-unit fail-closed gates; exact owner/count/coverage/
cutoff/denominator/opportunity/dedup/comparability/lifecycle/visibility/Query
semantics; deterministic replay; D09 focused plus D07/D08, full R4 and R1-R3
regressions; Ruff/compile/export/cache checks; TCP 8911 stopped; and an
independent Luna/max `ACCEPT_D09_RUNTIME` on a byte-stable snapshot.

The result does not accept D10, R5/UI, product, real projects/models, production
or medical-writing.

## Current corrective gate (2026-08-16)

- Worker01 首版与 follow-up1 的 overfit 结果均未接受。
- Worker01 follow-up2 补齐 28-case 显式事实并达到 clean parity，但 Luna
  follow-up3 因数值 authority、Query policy/proof、source alignment 的
  fail-closed 缺口返回 `REVISE_D09_CORRECTED_FREEZE`。
- Codex 已完成受控修复并重新生成候选；证据见
  `context/medical_monitoring_r4_d09_fact_completeness_correction_20260816.md`。
- Worker02/03 仍为 LOCKED；仅原 Luna verifier 对当前 SHA 返回
  `ACCEPT_D09_CORRECTED_FREEZE` 后才可解锁 Worker02。

### Gate disposition

2026-08-16 原 Luna verifier 已返回 `ACCEPT_D09_CORRECTED_FREEZE`，报告：
`runs/review/medical_monitoring_r4_d09_artifact_freeze_luna_followup4_20260816.md`。
Worker01 与 artifact 正式重冻结；Worker02 现解锁，Worker03 继续锁定。

### Worker02 disposition

2026-08-16 独立 Luna verifier 已对当前 byte-stable snapshot 返回
`ACCEPT_D09_WORKER02_PROJECTION`。权威记录：
`context/medical_monitoring_r4_d09_worker02_projection_acceptance_20260816.md`。
Worker02 正式冻结；Worker03 现解锁，并继续保持 D10、R5/UI、真实项目、
产品服务、生产和医学写作冻结。

### Final runtime disposition

2026-08-16，Worker03 closure、Codex 纠偏和同一独立 verifier 的连续攻击复测
已完成。最终裁决为 `ACCEPT_D09_RUNTIME`；权威记录：
`context/medical_monitoring_r4_d09_runtime_final_acceptance_20260816.md` 与
`runs/review/medical_monitoring_r4_d09_runtime_final_review_20260816.md`。
D09 runtime 正式冻结，只解锁 D10 contract discovery；D10 runtime、R5/UI、
真实项目/模型、产品服务、生产和医学写作继续锁定，8911 保持停止。
