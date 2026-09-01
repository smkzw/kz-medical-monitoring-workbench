# Codex Main-Venue Plan: mm_r7_slice_05_background_recovery_contract_20260828

Date: 2026-08-28
Objective: 独立审查 R7 Slice-05 后台执行与中断恢复合同草案：验证单一进度事实源、SQLite 原子所有权/租约、进程重建、取消与继续、旧 owner 回调、依赖调度、一致快照和延后真实模型 retry 的边界；只读审查，不修改代码，不启动服务/模型/真实项目，不触碰前端或医学写作。

## Task Decomposition

1. 两席独立映射草案到 R1 Store/background/capability recovery 事实。
2. 用崩溃窗口、双 owner、过期 lease、取消竞态、revision 切换和依赖图反例挑战。
3. 区分本切可诚实实现的 synthetic resume 与 Slice-06 才能定义的模型 retry。
4. Codex 汇总并冻结最小合同；合同通过后再初始化实施包。

## Source Packet

- Slice-05 合同草案与 Slice-04 验收记录。
- R1 background/store/capability recovery 源码与测试。
- R7 runtime adapter、产品路由、System Design §§12/15。

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_pi_antigravity` | `google-antigravity` | `gemini-3.7-flash` | `runs/conference/mm_r7_slice_05_background_recovery_contract_20260828/general_pi_antigravity.md` |
| `general_grok46` | `grok-build` | `grok-4.6` | `runs/conference/mm_r7_slice_05_background_recovery_contract_20260828/general_grok46.md` |

## Conference Panel Coordination

- No sub-venue chair. Codex leads the assigned panel directly.

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- 运行器完成后补录。

## Codex Verification Checklist

- [ ] 两席完整独立输出或明确终止状态
- [ ] 控制状态不成为第二套进度事实
- [ ] 所有权/租约/旧回调/取消竞态有可测试语义
- [ ] 不伪造 terminal retry 或 exactly-once
- [ ] 验收矩阵可在不启动服务/模型/真实项目条件下执行
