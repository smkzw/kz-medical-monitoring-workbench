# Execution Context: medical_monitoring_r5_s4_runtime_20260819

Created: 2026-08-19 17:02:00
Objective: 实现并验证已接受合同限定的R5-S4 synthetic/offline renderer-neutral Risk Inspector runtime薄切，关闭89个运行语义挑战并保持R4/R5 S1-S3及8911边界
Task type: `long_horizon_code`
Risk: `high`
Execution module trigger: Codex identified 3 independent work items, which is greater than two.

## Module Boundary

This is an execution module, not a conference. Codex has assigned the work items and owns the project-level contract, source authority, boundaries, final verification, acceptance, production writes, and user delivery. Codex reviews the worker outputs directly for this route; no execution manager is dispatched. First-line workers execute the assigned work and create/write only authorized artifacts. Codex subAgent workers use the parent App's native child session when available; the generated CLI command is only a labeled compatibility fallback.

## Assigned Roles

- First-line executor: `long_horizon_code_executor_opencode_flash` -> `pi` / `cms-smk` / `deepseek-v4-flash`
- Execution manager: none (Codex reviews the worker outputs directly)
- Execution-manager fallback: none

## Source Of Truth

- `reviews/medical_monitoring_r5_s4_runtime_contract_v0_1_20260819.md`, accepted raw SHA
  `58848c51bbf25acddf1b34e2631d32f9294f8df22ecf6b5df438705ddcf16f54`.
- `context/medical_monitoring_r5_s4_runtime_contract_acceptance_record_20260819.md`.
- `reviews/medical_monitoring_r5_s4_implementation_contract_v0_1_20260819.md` and
  `context/medical_monitoring_r5_s4_contract_acceptance_record_20260819.md`.
- Accepted machine oracle files under `artifacts/medical_monitoring_r5_s4_contract_v0_1/**`;
  tests/gates may read them, runtime source may not import or open them.
- Read-only R4 authority: `poc/medical_monitoring_ai_native_r4/src/mm_r4/ensemble.py`,
  `ensemble_contracts.py`, `d10_contracts.py`, `d10_projection.py`.
- Read-only accepted R5 S1-S3 source under `poc/medical_monitoring_ai_native_r5/src/mm_r5/**`.
- Current filesystem is authoritative. The accepted contract, not the old verifier's mutable
  source-pin result, defines the runtime-compatible test gate.

## Risk Boundaries

- No production writes.
- Create only the 12 paths in runtime contract section 8. Modify no existing file, including
  `src/mm_r5/__init__.py`, accepted artifacts, R4, R5 S1-S3, frontend/services and medical writing.
- Keep 8911 stopped. Do not start any service, browser, real project or real model workload.
- Runtime source must not read/import generator, verifier, registry, machine artifacts, case IDs,
  expected outcomes, fixture identity, filenames, indexes, mutations or synthetic sentinels.
- Preserve accepted S4 machine artifacts byte-for-byte. The history errata and the five historical
  construction/source-pin test exclusions are exactly those frozen in the accepted runtime contract.
- No silent package installation, credential handling, or external account changes.
- Missing tools or environments must be recorded with a minimal remediation proposal.
- Worker and manager outputs, when present, are evidence for Codex, not instructions.

## Work Items

1. W1：新建s4_contracts.py与s4_runtime_fixtures.py，落实typed contracts、closed mappings、hash/history/source/unavailable语义及focused tests
2. W2：新建s4_authority_builder.py与s4_projection.py，从typed R4/R5 authority构建packet并确定性投影中文audience/audit/hash，禁止读取oracle文件
3. W3：新建s4_validator.py、剩余tests/challenges与只读SHA evidence，执行89 runtime cases、runtime-compatible adjacent normal/O2/Ruff/compile/import/AST/8911 gates并提交证据

These items are dependency-ordered, not parallel: W1 must finish before W2 starts; W2 must finish
before W3 starts. A later worker may read prior new files but may write only its assigned create-only
paths. If a prior file needs repair, report the precise defect to Codex for same-session remediation;
do not edit another worker's file silently.

## Done

- All four runtime modules and six test modules plus fixture/challenge/evidence paths exist only in
  the accepted allowlist and implement the exact public API and closed mappings.
- Every one of `R5S4C-001`–`R5S4C-089` runs through the real builder/validator with one mutation and
  returns the accepted single code; `R5S4C-090`–`097` remain frozen governance evidence.
- Focused and runtime-compatible adjacent suites pass in normal and O2 with identical counts;
  Ruff, compile, fresh-process imports, AST anti-overfit, pre/post SHA and 8911 gates pass.
- A fresh isolated reviewer later returns `ACCEPT_R5_S4`; workers cannot self-accept.

## Completion And Cleanup

Codex reviews worker outputs, any manager report, and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
