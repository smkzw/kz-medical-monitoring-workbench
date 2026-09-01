# Codex Main-Venue Plan: mm_r7_slice09e_implementation_acceptance_20260831

Date: 2026-08-31
Objective: 独立审阅 R7 Slice-09E 本地分发与数据处置壳层的实际源码、测试与执行证据；核查其是否严格限于合成离线验收，是否存在并发升级、端口归属、路径身份、卸载数据处置、医学写作隔离、过度工程化或虚假完成声明；仅在所有 P0-P2 阻断关闭且证据充分时接受。

## Task Decomposition

1. 依据冻结合同逐条映射实际源码、测试和证据。
2. 独立挑战并发升级、端口归属、根路径身份和卸载数据处置边界。
3. 核查发布清单是否排除医学写作、凭据、真实项目、数据库、缓存和日志。
4. 区分合成离线验收与真实可安装/可运行发布物，阻止夸大完成声明。
5. Codex 复现或新增任何决定性检查，关闭 P0-P2 后才形成验收记录。

## Source Packet

见 `context/mm_r7_slice09e_implementation_acceptance_20260831_conference_context.md` 的 Source Of Truth。该包不含真实研究项目、模型输出、浏览器证据或医学写作源码。

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_single_object` | `cms-router` | `minimax-m3` | `runs/conference/mm_r7_slice09e_implementation_acceptance_20260831/general_single_object.md` |

## Conference Panel Coordination

- Preferred browser advisory chair: `chatgpt-web-pro-advisory` via `codex-with-chatgpt` (`Pro` / `GPT-5.6 Sol`). Codex remains the formal packet chair and final authority; the browser role is not dispatched through the runner.
- No sub-venue chair. Codex leads the assigned panel directly.

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- 初始化：2026-08-31 10:32 CST。
- 由 runner 单次硬等待至 120 分钟；仅在终态失败或同会话补充后仍无有效输出时按冻结链回退。

## Codex Verification Checklist

- [ ] conference preflight 通过并保留实际 route/session 证据
- [ ] 审阅者直接读取源码、合同和测试，而非仅复述执行报告
- [ ] P0-P2 已关闭；P3/P4 有明确处置
- [ ] 44 项焦点测试、R1+R7+09E 联合回归、ruff、compileall 可复现
- [ ] 8911/5174/8984 保持停止
- [ ] 医学写作聚合哈希与实施前基线一致
- [ ] 最终措辞不越过“合成离线壳层”边界
