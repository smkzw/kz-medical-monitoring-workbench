# Execution context — R6 runtime slice-07 Agent Harness adapter

## Goal

在不改产品服务、前端、医学写作和真实项目的前提下，建立最小可验证的
ExecutionProfile/OMP Harness adapter，使医学监查默认 route 冻结为 MTPLX Qwen 3.8 medium，
并保留、真实证明 DeepSeek V4 Flash max 的显式选择能力。

## Source of truth

- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md`
- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md`
- `context/medical_monitoring_r6_runtime_slice_07_agent_harness_contract_20260828.md`
- `poc/medical_monitoring_ai_native_r6/`
- OMP 18.0.7 model catalog (`omp models <provider> --json`)，仅作公开模型目录证据。

## Allowed paths

- `poc/medical_monitoring_ai_native_r6/src/mm_r6/agent_harness.py`
- `poc/medical_monitoring_ai_native_r6/tests/test_agent_harness.py`
- `poc/medical_monitoring_ai_native_r6/evidence/r6_agent_harness_runtime_receipt.json`
- `poc/medical_monitoring_ai_native_r6/{README.md,src/mm_r6/__init__.py}`
- `poc/medical_monitoring_ai_native_r6/tests/{test_challenge_matrix.py,test_report_review.py,test_report_bundle.py,test_mode_output.py}`
  仅限 slice-07 create-only allowlist 邻接更新；
- 本 task 的 `context/`、`reviews/`、`metrics/`、`records/`、runner-owned `runs/`/`logs/`。

## Hard boundaries

- 不修改 `services/`、`frontend/`、医学写作子系统或任何真实项目文件。
- 不启动 8911/5174、产品服务、浏览器或 OCR。
- 不输出或落盘凭据值。
- 不把 provider/model/effort 写入 R6 医学业务对象。
- 不自动 fallback；DeepSeek 只能由显式 profile 选择。

## Work items

1. 实现 profile registry、分层冻结、别名映射和 deterministic identity。
2. 实现 OMP print adapter 的 catalog/preflight/argv/invoke/receipt/coverage fail-closed。
3. 实现离线验收矩阵、两条受控真实模型 smoke 证据和相邻保护检查。

## Done

- 合同矩阵通过，MTPLX 与 DeepSeek 两种 profile 身份精确；
- focused/full/optimizer/hash 确定性门禁通过；
- 两条 synthetic real-call receipt 可核验且不泄漏凭据；
- 医学写作 aggregate 不变，8911/5174 停止，产品/真实项目未触碰；
- independent review 和 Codex review 接受，且限制声明完整。

## Timeout and recovery

每条真实模型 smoke 最多 120 分钟；runner 长等待，不定频轮询。超时或终端失败保留原始
失败分类，只允许按同一 selector/effort 复核，不得静默换模型。Codex 最终验收。
