# Codex Execution Plan: medical_monitoring_r1_patient_journey_slice4_20260809

Objective: 在全新隔离 R1 切片实现共享访视轴的受试者医学旅程：同步 Profile/Timeline、风险锚点、证据回跳、中文原生、离线本地，并完成真实浏览器验收；不得修改 Slice 3、产品、医学写作、服务、共享运行库或真实项目

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | 定义合成访视/阶段/点与区间事件/风险锚点数据合同和确定性测试 | `runs/execution/medical_monitoring_r1_patient_journey_slice4_20260809/worker_01.md` |
| `worker_02` | 实现离线 Patient Journey 前端、共享访视轴、泳道、时间窗、风险与证据联动 | `runs/execution/medical_monitoring_r1_patient_journey_slice4_20260809/worker_02.md` |
| `worker_03` | 完成 Chromium/WebKit 多视口、键盘、无远程请求、中文受众语言和视觉验收 | `runs/execution/medical_monitoring_r1_patient_journey_slice4_20260809/worker_03.md` |

## Manager

| Role | Provider | Model | Report |
|---|---|---|---|
| `visual_manager_cursor` | `cursor-cli` | `auto` | `runs/execution/medical_monitoring_r1_patient_journey_slice4_20260809/manager.md` |

## Codex Acceptance

1. Verify all writes are confined to the authorized new slice, browser evidence and runner-owned paths; compare Slice 3/protected hashes.
2. Read the final data contract and source; run focused deterministic tests, current R1 tests and Slice 3 tests.
3. Run or inspect Chromium/WebKit multi-viewport evidence, network/console/error logs, keyboard/a11y checks and audience-language scan.
4. Reopen at least the wide journey overview, medium risk-evidence state and 1280×800 screenshot; inspect spatial risk anchoring, visit-axis legibility, first-screen hierarchy, Chinese labels and overflow.
5. Reject completion if Profile/Timeline merely remain independent lists, risk cards are not spatially anchored, fixture rules leak into renderer, evidence cannot be reached, or browser claims lack real artifacts.
6. Update review/metrics/context, run review gate, archive execution artifacts only after acceptance, and retain the new slice as an isolated R1 POC rather than product code.
