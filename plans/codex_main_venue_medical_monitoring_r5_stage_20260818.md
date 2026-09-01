# Codex Main-Venue Plan: medical_monitoring_r5_stage_20260818

Date: 2026-08-18
Objective: 按 System Design v1.1 与 R0-R8 计划冻结并连续实施 R5 风险驾驶舱、中心图谱与 Subject Workspace/Patient Journey，保护医学写作，先合同后最小纵切，最终以真实浏览器和资深医学监察员任务验收

## Task Decomposition

1. 审计现有产品医学监查、R1 Journey 与 R4 投影，确认复用/淘汰边界。
2. 已冻结 R5 用户任务、信息架构、聚合口径、共享时间状态、中文文案、视觉编码和浏览器验收合同。
3. 隔离 stage reviewer 已在稳定 SHA 上给出 `ACCEPT_R5_CONTRACT`；仅解锁 S1。
4. 建立 R5 隔离/可迁移最小纵切：项目变化优先风险 → 中心图谱 → Risk Inspector → Subject Workspace/Journey → 来源。
5. 运行数据合同、组件、相邻 R4、构建和静态禁词检查；审计实际变更边界。
6. 临时启动产品浏览器环境，按资深医学监察员任务进行桌面 Playwright/视觉审阅；修复后复验并停止 8911。
7. 形成阶段 acceptance/pause record，并按计划进入剩余 R5 迭代，不宣称真实项目或生产完成。

## Source Packet

- System Design v1.1 §§10–12；Implementation Plan v1.1 §9。
- R4 stage acceptance 与 D09/D10 project/site projection contracts。
- Patient Journey research、R1 Slice 4、MG-K10 Timeline/Profile 视觉合同。
- 当前 frontend medical-monitoring、App route state、subject views/models/API contracts。
- Product Design saved-context preflight：无额外 saved context；不引入新视觉来源。

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `visual_pi_k3_256k` | `kimi-code` | `k3-256k` | `runs/conference/medical_monitoring_r5_stage_20260818/visual_pi_k3_256k.md` |

## Conference Panel Coordination

- No sub-venue chair. Codex leads the assigned panel directly.

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- 仅在上下文和 prompt 预检完成后派发；单次 hard wait 120 分钟。
- 慢响应保持 pending；只在终态或硬等待返回时检查，不固定轮询。
- 仅对可操作缺口使用同一 session follow-up；fallback 必须记录原因。

## Codex Verification Checklist

- [x] R5 合同覆盖计划步骤与完成证据，且未复制或伪造 R4 权威。
- [ ] 首屏任务与单跳下钻可用中文业务语言表达，禁词静态门完整。
- [ ] 项目/中心数字可从分子、分母、coverage、cutoff 重建。
- [ ] Journey/Profile/Timeline 共享时间窗与风险/来源锚点。
- [ ] desktop-first 信息密度、视觉层级、键盘/非颜色编码和窄屏降级明确。
- [ ] 医学写作无改动；真实项目/模型、生产与安全专项未扩入。
- [ ] 最小纵切测试、构建、真实浏览器与独立视觉/医学 QC 全部留证。
