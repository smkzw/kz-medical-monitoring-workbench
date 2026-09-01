# Codex Main-Venue Plan: mm_r7_slice07c4_user_product_loop_contract_20260829

Date: 2026-08-29
Objective: 独立审查 R7 Slice-07C-4 中文产品闭环合同：重点挑战公开结果上下文桥、四步向导、历史/主动作、离页恢复、结果看板与 Patient Journey 同身份贯通、中文/桌面视觉验收；只读，不修改产品源码。

## Task Decomposition

1. 核对 07C 总合同、07C-3 接受边界与现有 R5/R7 产品接口。
2. 审查四步向导、历史/主动作、离页恢复、进度和中文失败态是否适合资深医学监察员。
3. 挑战公开 result context 到既有 R5 overview/Journey/source 的身份闭环与 fail-closed 行为。
4. 挑战项目→中心→风险/流向→Journey 的同身份导航、横向访视轴和三视口视觉验收矩阵。
5. Codex 逐项裁决 findings；必要时在同一 session 补发纠偏复核，冻结后才进入实现。

## Source Packet

- `reviews/medical_monitoring_r7_slice07c4_user_product_loop_contract_v0_1_20260829.md`
- 07C v0.1/v0.2 总合同与 07C-3 接受记录。
- 现有 R5 页面、adapter、route state、Subject Flow/Journey 与 07A progress 组件。
- R7 product router 的 options/rules/prepare/history/progress/result-entry 及测试。

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `visual_single_object` | `grok-build` | `grok-4.6` | `runs/conference/mm_r7_slice07c4_user_product_loop_contract_20260829/visual_single_object.md` |

## Conference Panel Coordination

- No sub-venue chair. Codex leads the assigned panel directly.

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- 同一 session `b50d6481-6614-4fbe-800c-8a3a55530e9c` 完成四轮主审及定向复核；无 fallback。
- Round 1/2 为 `REVISE`，Round 3 仅余三个精确 P0，Round 4 `ACCEPT`；慢响应均按 7200 秒硬等处理。

## Codex Verification Checklist

- [x] reviewer 输出完整 schema、可追溯 session/route/runner 证据。
- [x] 公开 token 不泄露内部 run/authority/receipt 身份，R5 读取仍为唯一 authority。
- [x] 四步向导与三态主动作不复制服务端业务判断。
- [x] 离页恢复和 MTPLX 长等待不被前端误判失败。
- [x] 结果看板与 Journey 复用既有横向访视轴和八域事件编码。
- [x] 1280/1440/1920 ego(lite) 验收定义覆盖中文、密度、交互、空/错态与页面溢出。
