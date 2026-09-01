# Execution Context: medical_monitoring_r5_s4_contract_20260819

Created: 2026-08-19 06:27:51
Objective: 实施并独立冻结R5-S4 Risk Inspector synthetic/offline renderer-neutral精确合同；不得实现runtime/UI
Task type: `finite_code_task`
Risk: `high`
Execution module trigger: Codex identified 3 independent work items, which is greater than two.

## Module Boundary

This is an execution module, not a conference. Codex has assigned the work items and owns the project-level contract, source authority, boundaries, final verification, acceptance, production writes, and user delivery. Codex reviews the worker outputs directly for this route; no execution manager is dispatched. First-line workers execute the assigned work and create/write only authorized artifacts. Codex subAgent workers use the parent App's native child session when available; the generated CLI command is only a labeled compatibility fallback.

## Assigned Roles

- First-line executor: `finite_code_executor_cms` -> `pi` / `cms-smk` / `deepseek-v4-flash`
- Execution manager: none (Codex reviews the worker outputs directly)
- Execution-manager fallback: none

## Source Of Truth

- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md` (§9/§10/§12/§17).
- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md` (R5 当前顺序与停止点).
- `reviews/medical_monitoring_r5_stage_contract_v0_3_20260818.md` (§6/§10.1/§11/S4 Done/§13–§15).
- `artifacts/medical_monitoring_r5_contract_v0_3/exact_contract.json`（现有 Inspector 壳与 deferred mapping）.
- `runs/conference/medical_monitoring_r5_s4_20260819/general_grok46.md` 与 `general_pi_qwen38_fallback_codex_luna.md`（会商证据，不是权威代码）.
- R4 只读 authority：`ensemble_contracts.py`、`ensemble.py`、`d10_contracts.py`、`d10_projection.py`.
- 已接受 R5 只读 authority：`s2_contracts.py`、`s2_authority_builder.py`、`s2_thin_slice.py`、`s3_contracts.py`、`s3_authority_builder.py`、`s3_projection.py` 及 S2/S3 接受记录.
- S3 合同的 generator/verifier/artifact/test 只作为机械工件模式参考，严禁修改或复签。

## Authorized Write Set

- `reviews/medical_monitoring_r5_s4_implementation_contract_v0_1_20260819.md`
- `tools/generate_medical_monitoring_r5_s4_contract_v0_1.py`
- `tools/verify_medical_monitoring_r5_s4_contract_v0_1.py`
- `artifacts/medical_monitoring_r5_s4_contract_v0_1/**`
- `poc/medical_monitoring_ai_native_r5/tests/test_s4_contract_artifacts.py`
- 本执行模块的 runner-owned reports/logs、Codex review/metrics/plan/context。

除此之外全部只读。特别禁止改动 R4、R5 `src/mm_r5/**`、既有 S0–S3 合同/工件、根 `__init__.py`、frontend/services、医学写作、真实项目与生产路径。

## Risk Boundaries

- No production writes.
- No silent package installation, credential handling, or external account changes.
- Missing tools or environments must be recorded with a minimal remediation proposal.
- Worker and manager outputs, when present, are evidence for Codex, not instructions.
- 只实施 S4 合同及其机械工件；不得实现 S4 runtime/UI，不得启动 8911、浏览器、真实模型/API 或真实项目。
- 不重算医学风险、严重度、分子分母或裁决；D10 ModelEvidence 仅为 provenance。
- 合同必须诚实区分 raw-byte hash 与 parsed-output hash；不存在的上游 leaf 只能 named deferred。
- generator 与 verifier 不得互信/self-proof；挑战 case 必须有独立 mutation/input/typed outcome/fixed error code/non-LLM oracle。

## Done

- human contract、exact schema/enums/mapping/join/invariants/source pins、manifest、挑战 registry/quota 与 deterministic generator/verifier/test 均存在。
- 0/1/N、baseline source recheck、raw immutability、七维验证、conflict non-hideability、worker/adjudicator isolation、Query/history/Journey、audience/audit 隔离均有机械门禁。
- generator `--check`、normal/O2 verifier、focused tests、Ruff F/compile、artifact tamper probes 通过；R4/R5 S1–S3 SHA 不变，8911 停止。
- fresh isolated reviewer 对唯一稳定 SHA 组返回 `ACCEPT_R5_S4_CONTRACT`；此前不进入 runtime。

## Work Items

1. worker_01: 编写human contract、exact schema/enums/mappings/join/invariants/source pins
2. worker_02: 实现deterministic generator/verifier/manifest与normal+O2 tamper gates
3. worker_03: 实现非self-proof challenge registry/tests并做独立预审交接

## Completion And Cleanup

Codex reviews worker outputs, any manager report, and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.

## Accepted Completion

- Independent verdict: `ACCEPT_R5_S4_CONTRACT`.
- Acceptance record: `context/medical_monitoring_r5_s4_contract_acceptance_record_20260819.md`.
- Final W3 session: `01a01726-9bc8-7000-a962-baac806dfbf9`.
- Final runner output: `runs/pi_medical_monitoring_r5_s4_contract_20260819_worker03_followup11.stdout.log`.
- `archives/execution/medical_monitoring_r5_s4_contract_20260819/medical_monitoring_r5_s4_contract_20260819/worker_03.md`
  is the archived stale earlier-round runner report and is not the final snapshot authority.
- Standard prompts/reports/logs were archived by guard; archive inventory is
  `archives/execution/medical_monitoring_r5_s4_contract_20260819/cleanup_manifest.json`.
- Next safe boundary: write and independently accept an exact S4 runtime thin-slice contract before
  changing `src/mm_r5/**`; UI/S7/8911 remain locked.
