# Codex Main-Venue Plan: medical_monitoring_r1_background_progress_shell_acceptance_20260810

Date: 2026-08-10
Objective: 独立挑战并验收隔离 R1 后台医学监查进度 shell，复核实际工作去重、权威进度只读投影、离页/刷新恢复、中文受众语言和真实浏览器视觉证据

## Task Decomposition

1. 主会场冻结当前实现与测试哈希，保留纠偏前的并发重复执行复现作为证据。
2. 独立 participant 只读审查并亲自复现关键合同，给出 VETO/ACCEPT。
3. Codex 核对 participant 的证据，运行 core/adjacent/UI 回归，完成真实 Chromium 和截图验收。
4. 只在无开放 P0-P4 时更新 evidence/context/plan/review/metrics，且不声称 R1 总体完成。

## Source Packet

- 会商 context 中列出的冻结源、聚焦测试和三张视觉证据。
- 主会场已验证：R1 core `285 passed`；AE/MH `18 passed`；Patient Journey `16 passed`；Ruff/compileall 通过。
- 主会场 Chromium：1440×900 与 900×700 无溢出/截断，总体及六阶段进度条比率 1.0，console 0 error/0 warning。

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `visual_pi_k3_256k` | `kimi-code` | `k3-256k` | `runs/conference/medical_monitoring_r1_background_progress_shell_acceptance_20260810/visual_pi_k3_256k.md` |

## Conference Panel Coordination

- No sub-venue chair. Codex leads the assigned panel directly.

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- Round 1 completed in 504.261 s and was incorporated as a VETO.
- After a bounded repair, one same-session follow-up completed in 187.2 s and returned ACCEPT.
- No participant timed out, no late output was discarded, and no fallback route was used.

## Codex Verification Checklist

- [x] 并发三 facade 实际 `unit_step` 从 24 次纠偏为 8 次，每工作项 1 次。
- [x] R1 core 285，AE/MH 18，Patient Journey 16。
- [x] scoped Ruff 与隔离 compileall。
- [x] 真实 Chromium 返回/刷新、数字/进度条、语言、溢出、console。
- [x] 临时端口关闭；8911 无监听。
- [x] 独立 participant 首轮 VETO：Store 故障导致 worker 静默死亡与未公开的重复执行。
- [x] 主会场处置：worker 记录异常并自动续跑；合同明确故障恢复为 at-least-once，并向 `unit_step` 传入稳定幂等键；新增故障注入回归。
- [x] 视觉处置：去除会使进度条短暂滞后数字的过渡；失败与受阻使用不同色调。
- [x] 同一 participant session 第二轮终态与主会场处置：`ACCEPT`；主会场最终接受本切片。
