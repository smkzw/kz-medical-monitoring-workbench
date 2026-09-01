# Execution Context: medical_monitoring_r4_d09_runtime_20260815

Created: 2026-08-15 22:29:42
Objective: 在 R4 POC 内实现并独立验收冻结 D09 v0.5 的 179-case synthetic/offline 中心模式 runtime，保持 8911 停止且保护医学写作及真实项目
Task type: `long_horizon_code`
Risk: `high`
Execution module trigger: Codex identified 3 independent work items, which is greater than two.

## Module Boundary

This is an execution module, not a conference. Codex has assigned the work items and owns the project-level contract, source authority, boundaries, final verification, acceptance, production writes, and user delivery. Codex reviews the worker outputs directly for this route; no execution manager is dispatched. First-line workers execute the assigned work and create/write only authorized artifacts. Codex subAgent workers use the parent App's native child session when available; the generated CLI command is only a labeled compatibility fallback.

## Assigned Roles

- First-line executor: `long_horizon_code_executor_opencode_flash` -> `pi` / `opencode-go` / `deepseek-v4-flash`
- Execution manager: none (Codex reviews the worker outputs directly)
- Execution-manager fallback: none

## Source Of Truth

- Frozen D09 v0.5 contract and accepted 179-case catalog/quota/registry/oracle
  chain recorded in
  `context/medical_monitoring_r4_d09_artifact_freeze_acceptance_record_20260815.md`.
- Existing accepted D08 runtime structure and tests under
  `poc/medical_monitoring_ai_native_r4/src/mm_r4/d08_*` and
  `poc/medical_monitoring_ai_native_r4/tests/test_d08_*` are implementation
  conventions, not authority over D09 semantics.
- Current filesystem is authoritative. Worker reports are evidence only.

## Risk Boundaries

- Write only new D09 files/tests and the later D09 package-export block declared
  per worker in the plan. D01-D08, R1-R3, product, frontend, service, real-project
  and medical-writing paths are read-only or out of scope.
- Frozen D09 artifacts, generators, contract and artifact tests are read-only.
- Synthetic/offline only; no service, TCP 8911, real patient/project data or
  model endpoint. No security design/testing.
- No silent package installation, credential handling or external account change.
- Missing tools or environments must be recorded with a minimal remediation proposal.
- Workers never accept their own output; Codex owns freeze and final verification.

## Work Items

1. Worker 01: typed contract, artifact test adapter, deterministic evaluator, exact core/trace/source oracle parity
2. Worker 02: renderer-neutral risk, Chinese Query, hotspot, deep-link, visibility, count and R2 handoff projection
3. Worker 03: public exports, mutation/anti-overfit/replay/closure suites and focused/adjacent/full regression

## Completion And Cleanup

Codex reviews worker outputs, any manager report, and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
