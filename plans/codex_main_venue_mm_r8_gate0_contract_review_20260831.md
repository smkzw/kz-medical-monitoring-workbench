# Codex Main-Venue Plan: mm_r8_gate0_contract_review_20260831

Date: 2026-08-31
Objective: 对医学监查 R8-0 联合准入合同 v0.1 做 fresh-context 独立挑战：检查真实资料解锁顺序、来源零写入、输出隔离、独立 harness/LLM 责任、防硬编码与过拟合、真实应用/通知/§15.4、full/incremental、P0-P4 缺陷传播及 clean-streak reset。不得读取真实项目路径、不得运行真实模型/服务/浏览器、不得修改产品源码；输出可定位 P0-P4 发现和最小修订，不能声称最终接受。

## Task Decomposition

1. 独立检查联合合同的 gate 顺序及是否存在提前读取真实资料/调用模型/启动浏览器的路径。
2. 独立检查来源身份、A/B inventory、零写入、manifest、输出隔离和 re-admission 的可机验性。
3. 独立检查 Codex/开发者与 harness/LLM/parser/validator/adjudicator 的职责是否可能被越权绕过。
4. 独立检查 anti-overfit 隐藏挑战能否发现项目、药物、疾病、量表、风险、列名和布局硬编码。
5. 独立检查一键应用、通知二选一、§15.4、ego(lite)、full/incremental、P0-P4、传播和 clean-streak 的声明边界。
6. Codex 按发现最小修订，重新计算摘要，必要时用同一 session 复审，不自行扩大至实现或真实验证。

## Source Packet

- `reviews/medical_monitoring_r8_gate0_source_admission_anti_overfit_contract_v0_1_20260831.md`
- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md`
- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md`
- `context/medical_monitoring_r7_phase_acceptance_record_20260831.md`
- `reviews/codex_execution_mm_r8_gate0_contract_draft_20260831_review.md`
- `runs/execution/mm_r8_gate0_contract_draft_20260831/worker_01.md`
- `runs/execution/mm_r8_gate0_contract_draft_20260831/worker_02.md`
- `runs/execution/mm_r8_gate0_contract_draft_20260831/worker_03.md`

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_single_object` | `cms-router` | `minimax-m3` | `runs/conference/mm_r8_gate0_contract_review_20260831/general_single_object.md` |

## Conference Panel Coordination

- Preferred browser advisory chair: `chatgpt-web-pro-advisory` via `codex-with-chatgpt` (`Pro` / `GPT-5.6 Sol`). Codex remains the formal packet chair and final authority; the browser role is not dispatched through the runner.
- No sub-venue chair. Codex leads the assigned panel directly.

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- 120-minute runner hard wait；慢不等于失败。
- 首轮完成后由 Codex 决定是否同 session follow-up；仅在明确终态失败且恢复耗尽后使用 runner fallback。
- ChatGPT Web advisory 因 skill 入口缺失且本任务禁止浏览器而未实际启动；不阻断 declared executable panel。

## Codex Verification Checklist

- [ ] runner prompt preflight 通过。
- [ ] participant 未访问任何真实项目路径、模型、服务或浏览器。
- [ ] participant 输出包含最高影响发现、定位、严重度、最小修订和验收信号。
- [ ] Codex 独立核对合同与 System Design/R0-R8/R7 接受记录。
- [ ] 所有 P0-P4 合同发现已关闭或明确阻断冻结。
- [ ] 修订后摘要与状态一致，旧摘要标记 superseded。
- [ ] review-gate 通过，且不误称 R8-0/真实项目接受。
