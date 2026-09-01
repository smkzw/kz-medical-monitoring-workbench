# Codex Main-Venue Plan: medical_monitoring_r3_kernel_acceptance_20260810

Date: 2026-08-10
Objective: 独立工程与医学监查语义验收 R3 Study Intelligence 合成 POC 快照：严格复核来源权威、异构 listing 画像/mapping/身份、全量快照增量 diff、自然语言规则生命周期、反过拟合及中文原生边界；仅读、不做系统安全审计、不触碰医学写作/产品/真实项目、不启动 8911。

## Task Decomposition

1. 参与者 1 以工程对抗审阅视角检查数据合同、不变量、来源/身份/生命周期和测试盲区。
2. 参与者 2 以资深医学监查语义视角检查全量导出增量、消失记录、规则范围、中文原生和反过拟合边界。
3. Codex 比对独立报告，只对可复现阻断项做最小修订；随后重跑决定性/全量检查并复核摘要、缓存、8911。
4. 通过时形成 R3 合成内核独立接受记录；不把它表述为真实项目、R4 风险分析、R5 UI 或 R3 整体生产完成。

## Source Packet

- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md`
- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md`
- `context/medical_monitoring_r3_study_intelligence_20260810_context.md`
- `reviews/medical_monitoring_r3_external_solution_discovery_20260810.md`
- `poc/medical_monitoring_ai_native_r3/src/mm_r3/*.py`
- `poc/medical_monitoring_ai_native_r3/tests/*.py`
- 只读上游：`poc/medical_monitoring_ai_native_r1/`、`poc/medical_monitoring_ai_native_r2/`

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_pi_qwen38` | `alibaba` | `qwen3.8-max` | `runs/conference/medical_monitoring_r3_kernel_acceptance_20260810/general_pi_qwen38.md` |
| `general_grok45` | `grok-build` | `grok-4.5` | `runs/conference/medical_monitoring_r3_kernel_acceptance_20260810/general_grok45.md` |

## Conference Panel Coordination

- No sub-venue chair. Codex leads the assigned panel directly.

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- 两个参与者均按 runner 120 分钟硬等待启动一次；运行中不固定间隔轮询、不因延迟重派。
- 仅在终态输出存在具体缺口时使用同 session follow-up；fallback 原因由 runner 记录。
- 完成后记录开始/结束、primary/fallback、session、终态及是否纳入裁决。

## Codex Verification Checklist

- [x] 两份报告均来自独立上下文，且未读取另一参与者输出。
- [x] 阻断项有源码定位、失败测试或最小可复现反例；意见型建议不冒充阻断。
- [x] R3 聚焦及全量 pytest 通过；运行前后审阅对象 SHA 稳定。
- [x] R1/R2 冻结摘要不变；R3 无 `__pycache__` / `.pytest_cache`。
- [x] 8911 无监听者；未读取真实项目、未修改产品/医学写作/R1/R2。
- [x] 接受结论明确限定为 R3 合成/隔离内核，并写明仍未验证的真实 listing、R4/R5 和视觉边界。
