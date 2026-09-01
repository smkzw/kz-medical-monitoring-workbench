# Codex Review: mm_r8_gate3_notification_decision_contract_20260831

Date: 2026-08-31
Delegated-agent output: `runs/codex-subagent_mm_r8_gate3_notification_decision_contract_20260831.md`

## Verdict

`REVISE_THEN_USE_AS_ADVISORY`.

子审阅对 capability、三元身份、幂等、点击无启动副作用、最小披露和 fail-closed 的建议可用；但其未读 G0 权威合同，将“应用内持久降级”误名为 Path B，并将多类上游终态折叠为 completed/failed。父 Codex 已依 G0 §§8.2、3.3 纠正，不直接接受该结论。

## Boundary Check

- 本次可执行路由为 Codex native subAgent，未通过 Hermes 传输，未静默替换 provider/model。
- native subAgent 声明只读取冻结上下文，未修改文件、启动服务/浏览器/模型或访问真实项目。
- 共享文件系统未出现该子任务的产品源码改动；当前工作区本身无 Git 元数据，因此不以 `git status` 作为边界证据。
- 生成 prompt 明确要求不以工具写入 runner-managed output；当前 App native-child transport 未将终端回答自动落到该路径。本评审不伪造 runner 产物，仅将可审核终端回答作为建议证据。

## Codex Verification

- 重开 G0 联合准入合同 §§3.3、8.2、9：确认 Path A/B 正式语义及原始终态保留要求。
- 重开 G2 接受记录：确认 G3 是唯一下一安全动作，真实通知/浏览器/模型/项目仍未接受。
- 核对实施计划 R7 步骤3、System Design §§15.1–15.4 及当前 UI：`App.jsx:1446` 显示“通知中心尚未开放”，进度面仅有页面内 `aria-live` 状态。
- 本阶段只是合同工作，按 G0 门禁不运行浏览器、服务、模型或真实项目；不存在应由本评审运行的产品测试。

## Delegated-Agent Output Review

- 可保留：capability 四状态、三元身份、通道失败不改写分析终态、系统通知最小披露、点击只导航、G5/G6 分层。
- 已纠正 1：G0 Path B 是“用户明确接受仅页面内状态”，不是应用内持久降级面。
- 已纠正 2：不将 `partial/final_partial/truncated/timed_out/cancelled/interrupted/blocked` 等折叠为泛化 `FAILED`。
- 已纠正 3：对上游 `complete` 仅在结果可访问后投影为通知合同的 `analysis_complete`，不把进程退出或通知入队当成完成。
- 已将上述纠正落入 `reviews/medical_monitoring_r8_gate3_notification_decision_contract_v0_3_20260831.md`，经 fresh-context 同 session 独立会商持续纠偏。

## Residual Risk

- 当前合同仍是待独立审阅草案，不能声称 G3 已锁定。
- App native-child 的 runner-managed 输出未自动落盘；不影响 Codex 重新打开权威源纠错，但该 init-task 不单独作为最终会商接受证据。
