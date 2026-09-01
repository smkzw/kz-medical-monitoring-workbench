# Codex Main-Venue Plan: mm_r7_slice09d_contract_acceptance_20260830

Date: 2026-08-31
Objective: 独立审阅 R7 Slice-09D 性能、容量与长任务恢复合同 v0.1。逐项挑战 corpus 分级与成本、process-cold/warm 和采样统计、correctness-first 停止、故障/恢复状态、中文用户投影、反过拟合、独立 harness/LLM 责任和 R8 source-admission。按 P0-P4 输出可定位问题；测试计数不能替代合同完整性。不得改文件、启动服务/模型/浏览器、读取真实项目或触碰医学写作/安全专项。

## Task Decomposition

1. 重开 v0.1 与 execution outputs；2. 独立 P0-P4 查缺；3. Codex 修订 v0.2；4. 同 session 复核直至清零；5. 冻结 SHA 与接受记录。

## Source Packet

09D v0.1/v0.2、09C 接受记录、阶段复盘、execution review/metrics、三份 worker outputs、四轮 conference outputs/logs。

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_single_object` | `codebuddy-cli` | `deepseek-v4-flash` | `runs/conference/mm_r7_slice09d_contract_acceptance_20260830/general_single_object.md` |

## Conference Panel Coordination

- No sub-venue chair. Codex leads the assigned panel directly.

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

四轮均完成并纳入；无 timeout/retry/fallback/late output，始终复用同一 session。

## Codex Verification Checklist

- [x] 固定网格、采样、预算、统计与停止语义。
- [x] 故障恢复、取消、进度与中文投影。
- [x] 反过拟合、coverage 重算、独立 harness/LLM 责任。
- [x] R8 evidence admission 非安全/权限系统。
- [x] 交付物、条款门、三端口与相邻回归边界。
- [x] 最终 P0-P4 全零和合同 SHA。
