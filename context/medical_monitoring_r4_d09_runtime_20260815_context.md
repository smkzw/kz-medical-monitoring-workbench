# Task Context: medical_monitoring_r4_d09_runtime_20260815

Created: 2026-08-15 22:28:09
Objective: 依据已冻结 D09 v0.5 合同和已接受 179-case artifact，在 R4 POC 内实现 synthetic/offline D09 中心重复模式与系统性风险 runtime，完成聚焦、相邻与独立验收；保持 8911 停止且不触碰真实项目、R5 UI、产品服务或医学写作
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Frozen D09 contract:
  `reviews/medical_monitoring_r4_d09_center_pattern_slice_contract_v0_5_20260814.md`
  (`9d20b99487260c286e5105ba1d1de6fb4e4d5af3f9a3faaee5df2e67f0907e40`).
- Accepted D09 artifact chain and tests listed in
  `context/medical_monitoring_r4_d09_artifact_freeze_acceptance_record_20260815.md`.
- Existing accepted R4 runtime conventions in
  `poc/medical_monitoring_ai_native_r4/src/mm_r4/d08_contracts.py`,
  `d08_evaluator.py`, `d08_projection.py`, package exports and D08 tests.
- Current filesystem is authoritative; worker reports are evidence, not acceptance.

## Scope

- In scope: synthetic/offline D09 typed runtime contract, deterministic
  evaluator, artifact-to-runtime test adapter, center-pattern risk/Query/
  hotspot/deep-link/count/visibility/R2-handoff renderer-neutral projection,
  package exports, exact 179-case oracle parity, mutation/determinism/closure
  tests and R4/D07/D08/R1-R3 adjacency regression.
- Out of scope: D10, R5/UI, product services, real projects/patient data,
  real model endpoints, cross-site ranking/inference, security design/testing,
  and all medical-writing files.

## Success Criteria

- Runtime never reads/imports the D09 catalog, oracle, registry, generators or
  acceptance tests and never branches on case/fixture/test identifiers,
  expected leaves, free-text descriptions or display labels.
- All 179 frozen cases parse through typed objects and exactly reproduce all
  expected, trace and source leaves with zero case-specific exceptions.
- Contract order is fail-closed: global admission failure emits only a gate;
  admitted-unit completeness failure emits exactly one not-evaluable unit;
  no risk/Query/Journey leaks through either path.
- Counts remain separated; same-origin dedup, coverage/L1 holes, cutoff,
  denominator/opportunity, comparability, counterevidence, visibility,
  lifecycle/handoff and Query redundancy/fanout semantics match v0.5.
- D09 focused, D07/D08 adjacency, full R4 and frozen R1-R3 pass; Ruff/compile,
  deterministic replay, public exports, cache and TCP 8911 checks pass.
- Fresh independent verifier accepts an immutable snapshot before D09 runtime
  is marked complete.

## Risk Boundaries

- Writable paths are limited to new D09 files under
  `poc/medical_monitoring_ai_native_r4/src/mm_r4/`, new D09 tests under
  `poc/medical_monitoring_ai_native_r4/tests/`, and the D09 export block in
  `poc/medical_monitoring_ai_native_r4/src/mm_r4/__init__.py`.
- Do not modify D01-D08, R1-R3, product/frontend/service, real-project or
  medical-writing files. Do not start 8911 or any service.
- Artifact JSON, generators, contract and artifact-freeze tests are frozen
  read-only inputs during runtime work.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.
- A provider catalog/auth/transport preflight is diagnostic, not a live capability verdict: timeout, auth refresh failure, malformed output, or a stale/incomplete catalog must be recorded and followed by one real route attempt. Explicit user-selected routes are not blocked merely because the catalog does not list them; only a missing executable or native transport boundary may stop before that attempt.

## Loop Log

- 2026-08-15 22:28:09: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-15: External-discovery gate reused the current local decision: the
  runtime method is fixed by the accepted D09 v0.5 contract and the already
  accepted D08 R4 architecture. No new dependency or architecture choice is
  being adopted, so fresh web discovery would not change this bounded slice.
- 2026-08-15: Artifact freeze accepted; D09 runtime is the sole unlocked next
  slice. Planned serial implementation: typed kernel/evaluator, audience and
  lifecycle projection, then integration/mutation/replay/adjacency closure.
