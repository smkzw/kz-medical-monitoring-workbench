# Codex Main-Venue Plan: medical_monitoring_r1_overall_acceptance_20260810

Date: 2026-08-10
Objective: 对隔离 synthetic 医学监查 R1 步骤1-13进行总体验收：逐项建立代码/测试/浏览器/独立审阅证据矩阵，识别仍断链或未证明项；只更新验收记录，不修改产品或医学写作源码，不启动8911，不运行真实项目，只有全部R1完成证据通过才允许进入R2

## Task Decomposition

1. Codex reconstructs a 13-row requirement→implementation→test→browser→review matrix from current files.
2. Two fresh-context participants independently try to falsify the matrix, with special focus on
   the audience/runtime seam, adapter tools/isolation contract, R4 stage classification and
   framework comparison completeness.
3. Codex compares both reports against newly rerun deterministic and browser checks, repairs only
   concrete R1 evidence/record defects, and issues the final isolated-R1 decision.
4. R2 may start only after an ACCEPT decision; protected product, medical-writing, real-project
   and port-8911 boundaries remain unchanged.

## Source Packet

- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md`
- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md`
- `poc/medical_monitoring_ai_native_r1/docs/R1_OVERALL_ACCEPTANCE_MATRIX.md`
- R1 source/tests, ADRs, failure/progress/capability/integrated-closure evidence and accepted reviews
- Current Playwright QC summaries/screenshots for Slice 3 and Patient Journey

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_pi_qwen38` | `alibaba` | `qwen3.8-max` | `runs/conference/medical_monitoring_r1_overall_acceptance_20260810/general_pi_qwen38.md` |
| `general_grok45` | `grok-build` | `grok-4.5` | `runs/conference/medical_monitoring_r1_overall_acceptance_20260810/general_grok45_round3.md`（前两轮中断后同会话恢复） |

## Conference Panel Coordination

- No sub-venue chair. Codex leads the assigned panel directly.

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- Both roles receive one 120-minute hard wait and 128 internal turns. Slow output remains pending.
- Same-session follow-up is allowed only for a concrete missing row, truncated report or actionable
  contradiction. Fallback is allowed only after runner-confirmed terminal failure/unavailability.
- Start/end/session/fallback/usage and incorporation decisions are recorded in conference metrics.

## Codex Verification Checklist

- [x] Current R1 core 327 passed（包含 lifecycle observer 根包公共导出回归）.
- [x] Current AE/MH audience 19 passed（12 data + 7 browser）.
- [x] Current Patient Journey 17 passed（10 data + 7 browser）.
- [x] Both current QC summaries have `overall_pass=true` and no defects.
- [x] Both audience JavaScript files pass `node --check`; Python compileall passed.
- [x] 8911 has no listener.
- [x] Both independent participant reports are terminal and reviewed; Grok recovery limits are recorded.
- [x] No R1 VETO remained; Pi/Qwen's performance-record objection was reproduced and corrected.
- [x] Main-venue visual review caught and fixed the audience-language defect missed by both participants.
- [x] Final matrix/review/metrics/recovery point are mutually consistent.
