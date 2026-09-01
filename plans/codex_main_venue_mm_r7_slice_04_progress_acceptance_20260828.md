# Codex Main-Venue Plan: mm_r7_slice_04_progress_acceptance_20260828

Date: 2026-08-28
Objective: 对 R7 Slice-04 耐久运行进度实现进行独立只读验收：逐条核对冻结契约、身份隔离、零I/O边界、幂等与回退阻断、post_lock冻结、中文产品投影、测试与证据真实性；仅报告可复现缺陷，不修改文件，不启动服务/模型/真实项目，不触碰医学写作子系统。

## Task Decomposition

1. 两名参与者分别从冻结契约逐项映射实现与测试，不读取彼此输出。
2. 对身份边界、构造期零 I/O、prepare 幂等、A→B→A 回退阻断、post-lock 冻结及中文安全投影做反例审查。
3. 仅在必要时运行离线测试或最小复现；不启动服务、模型或真实项目。
4. Codex 汇总可复现问题，执行最小修复并独立复验，最终决定有限验收。

## Source Packet

- 冻结契约：`context/medical_monitoring_r7_slice_04_durable_run_progress_contract_20260828.md`
- 实现：`poc/medical_monitoring_ai_native_r7/src/mm_r7/runtime_progress.py`、`services/api/app/medical_monitoring_r7_product_router.py`
- 测试：`poc/medical_monitoring_ai_native_r7/tests/test_runtime_progress.py`、`tests/test_medical_monitoring_r7_product_router.py`、`poc/medical_monitoring_ai_native_r7/tests/test_determinism_adjacent.py`
- 说明与证据：`poc/medical_monitoring_ai_native_r7/README.md`、`poc/medical_monitoring_ai_native_r7/evidence/r7_durable_progress_receipt.json`

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_pi_antigravity` | `google-antigravity` | `gemini-3.7-flash` | `runs/conference/mm_r7_slice_04_progress_acceptance_20260828/general_pi_antigravity.md` |
| `general_grok46` | `grok-build` | `grok-4.6` | `runs/conference/mm_r7_slice_04_progress_acceptance_20260828/general_grok46.md` |

## Conference Panel Coordination

- No sub-venue chair. Codex leads the assigned panel directly.

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- 待运行器完成后补录每个角色的开始/结束时间、有效模型、session、fallback 与采用状态。

## Codex Verification Checklist

- [ ] 冻结契约哈希与实际读取文件一致
- [ ] 两个独立参与者均返回完整报告或明确终止状态
- [ ] 所有可复现缺陷均由 Codex 复现、修复或明确限制
- [ ] 聚焦、R7、R1、R6 回归通过
- [ ] 医学写作 542 文件聚合哈希不变；8911/5174 无监听
- [ ] receipt、README、验收记录与实际证据一致
