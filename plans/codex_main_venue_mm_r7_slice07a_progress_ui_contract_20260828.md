# Codex Main-Venue Plan: mm_r7_slice07a_progress_ui_contract_20260828

Date: 2026-08-28
Objective: 独立审阅 R7 Slice-07A 医学监查真实进度与恢复界面合同：从懒惰、视觉敏感、数据敏感、风险敏感、中文原生且不熟悉计算机和AI的资深医学监察员视角，挑战信息层级、状态语义、真实进度、离页后台、停止/继续、错误恢复、无后端术语、可访问性和后续 ego(lite) 验收矩阵。不得实现代码，不得启动服务，不得运行真实项目；输出可执行的 P0-P4 修订意见。

## Task Decomposition

1. 核对合同是否把 R7 progress 响应作为唯一展示权威，并覆盖迟到响应、离页和稳定状态。
2. 从资深医学监察员视角审阅首屏信息层级、中文文案、动作可见性和异常恢复。
3. 审阅宽屏/窄屏、键盘、减弱动效及 ego(lite) 验收矩阵是否可执行。
4. 输出按 P0-P4 分级、指向具体条款的修订建议；Codex 独立复核后决定是否修改合同。

## Source Packet

- `reviews/medical_monitoring_r7_slice_07a_progress_ui_contract_v1_20260828.md`
- `context/medical_monitoring_r7_slice_06_review_and_slice07_plan_20260828.md`
- `frontend/AGENTS.md`
- `frontend/src/features/medical-monitoring/r5/MedicalMonitoringR5Page.jsx`
- `frontend/src/features/medical-monitoring/r5/medicalMonitoringR5Adapter.mjs`
- `frontend/src/features/medical-monitoring/r5/medicalMonitoringR5RouteState.mjs`
- `frontend/src/features/medical-monitoring/medicalMonitoringApi.mjs`
- `poc/medical_monitoring_ai_native_r7/src/mm_r7/runtime_progress.py`
- `tests/test_medical_monitoring_r7_product_router.py`

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `visual_pi_k3_256k` | `kimi-code` | `kimi-code/k3-256k` | `runs/conference/mm_r7_slice07a_progress_ui_contract_20260828/visual_pi_k3_256k.md` |

## Conference Panel Coordination

- No sub-venue chair. Codex leads the assigned panel directly.

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- Completed in two rounds on the same Kimi session; no fallback.
- Recorded runner durations: 125.818 s + 105.076 s; both completed inside the 120-minute boundary.

## Codex Verification Checklist

- [x] prompt preflight 通过。
- [x] runner 记录实际 provider/model/session 且输出非空、未截断。
- [x] 每项建议可追溯到合同或源代码现状。
- [x] Codex 独立核对接口字段、状态矩阵和用户可见中文。
- [x] 合同完成必要修订。
- [x] 本会商期间未改代码、未启动服务/浏览器、未运行真实项目。
- [ ] review-gate 与 validate-conference 通过。
