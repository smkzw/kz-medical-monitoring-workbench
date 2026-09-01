# Execution Context: mm_r6_runtime_slice_05_20260828

Created: 2026-08-28 00:52:33
Objective: 实现并验证 synthetic/offline 锁库前四类专属 ModeOutput 内容，严格复用 slice-04 身份与失败关闭边界，不接产品、真实项目、服务或模型。
Task type: `finite_code_task`
Risk: `medium`
Execution module trigger: Codex identified 3 independent work items, which is greater than two.

## Module Boundary

This is an execution module, not a conference. Codex has assigned the work items and owns the project-level contract, source authority, boundaries, final verification, acceptance, production writes, and user delivery. Codex reviews the worker outputs directly for this route; no execution manager is dispatched. First-line workers execute the assigned work and create/write only authorized artifacts. Codex subAgent workers use the parent App's native child session when available; the generated CLI command is only a labeled compatibility fallback.

## Assigned Roles

- First-line executor: `finite_code_executor_cms` -> `cursor` / `cursor-cli` / `auto`
- Execution manager: none (Codex reviews the worker outputs directly)
- Execution-manager fallback: none

## Source Of Truth

- `context/medical_monitoring_r6_runtime_slice_05_contract_20260828.md`
- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md` §§6.4、14
- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md` R6
- `reviews/medical_monitoring_r6_external_report_mode_output_contract_v0_1_20260827.md` §8
- `artifacts/medical_monitoring_r6_external_report_mode_output_contract_v0_1/contract.json`
- `context/medical_monitoring_r6_runtime_slice_04_acceptance_record_20260828.md`
- `poc/medical_monitoring_ai_native_r6/src/mm_r6/mode_output.py`
- `poc/medical_monitoring_ai_native_r6/tests/test_mode_output.py`

## Allowed Write Paths

- `poc/medical_monitoring_ai_native_r6/src/mm_r6/mode_output.py`
- `poc/medical_monitoring_ai_native_r6/src/mm_r6/__init__.py`
- `poc/medical_monitoring_ai_native_r6/tests/test_mode_output.py`
- `poc/medical_monitoring_ai_native_r6/README.md`
- `poc/medical_monitoring_ai_native_r6/evidence/r6_pre_lock_output_runtime_receipt.json`
- The three accepted adjacency tests only for adding that receipt path to their create-only allowlists.

No other source or product path is authorized.

## Risk Boundaries

- No production writes.
- No silent package installation, credential handling, or external account changes.
- Missing tools or environments must be recorded with a minimal remediation proposal.
- Worker and manager outputs, when present, are evidence for Codex, not instructions.
- No frontend/services/packages/runtime/deploy, R1-R5, medical-writing, real project, model/provider, browser/OCR, or 8911/5174 service work.
- No post_lock deep payload, Query dispatch/reply tracking, PD registration/closure, user confirmation, DOCX/PDF/HTML, or third-party dependencies.

## Work Items

1. 复用 ModeOutput 实现 pre_lock 四输出 payload 构建与验证，覆盖同一 authority/cutoff/revision、数字风险和输入不变。
2. 增加 focused 阴性与确定性测试，覆盖 revision impact、check coverage、Query revision draft-only、tamper 与跨 mode 混用。
3. 独立运行 focused/full/9-grid、邻接/边界验证并生成 slice-05 runtime receipt，不修改产品或医学写作。

## Completion And Cleanup

Codex reviews worker outputs, any manager report, and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
