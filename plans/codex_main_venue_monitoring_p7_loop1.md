# Codex Main-Venue Plan: monitoring_p7_loop1

Date: 2026-07-29
Objective: 独立审阅P7日常医学监查运行台账、批次输入绑定、独立AI门禁与最终医学确认设计，返回冲突点和风险点

## Task Decomposition

1. 两位参与者分别从工程完整性和医学监查可操作性视角独立审阅完整 P7 闭环。
2. 重点核对批次与风险链路是否真正共享同一输入身份，而不是仅由前端顺序串联。
3. 核对基线、diff、规则、AI、风险复核和最终确认在崩溃、并发、部分失败时是否可恢复。
4. 核对独立 AI 是否与医学写作共享产品配置且不依赖 Codex/subAgent/CLI harness。
5. 主席只比较参与者冲突和遗漏，形成可执行优先级，不重复无差异的完整审阅。
6. Codex 把会商结论与本地实现、测试和真实 API 证据交叉验证后决定修订。

## Source Packet

以 `context/monitoring_p7_loop1_conference_context.md` 的 Source Of Truth 为准。参与者可沿相邻
调用链扩展读取，但不得读取其他参与者输出或修改产品文件。

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_aishuo_cms` | `aishuo` | `cms-model` | `runs/conference/monitoring_p7_loop1/general_aishuo_cms.md` |
| `general_codebuddy_deepseek_pro` | `codebuddy-cli` | `deepseek-v4-pro` | `runs/conference/monitoring_p7_loop1/general_codebuddy_deepseek_pro.md` |

## Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_chair_pi_qwen38` | `alibaba` | `qwen3.8-max-preview` | `runs/conference/monitoring_p7_loop1/general_chair_pi_qwen38.md` |

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- 2026-07-29 16:59 CST 初始化。
- 参与者并行启动；按 60 分钟软等待、120 分钟大任务等待和 240 分钟主席硬等待处理。
- 慢响应保持 pending；仅终态错误、恢复循环无进展或结果不合格才走声明的 fallback。

## Codex Verification Checklist

- [ ] 参与者报告均可追溯到真实文件/方法。
- [ ] 主席明确列出参与者冲突、共同遗漏和建议优先级。
- [ ] 不采用与 P5/P6 合同冲突的风险身份或事实视图方案。
- [ ] 不将 `frozen` 与最终医学 `confirmed` 混同。
- [ ] P7 run 显式绑定 batch、baseline、mapping、rule pack、engine、diff algorithm。
- [ ] 首批、第二批、结构漂移、部分失败、重启和并发确认均有测试路径。
- [ ] 产品 AI 不依赖 Codex、subAgent 或 CLI Agent 传输。
- [ ] 采纳项必须由 Codex 在真实 API/浏览器/测试中验证；模型信心不是验收证据。
