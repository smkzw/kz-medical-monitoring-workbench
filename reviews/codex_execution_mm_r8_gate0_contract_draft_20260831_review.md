# Codex Execution Review: mm_r8_gate0_contract_draft_20260831

## Verdict

`ACCEPT_FOR_INDEPENDENT_CHALLENGE`。

三份 worker 输出均在边界内完成，且已由 Codex 合并为一份候选联合合同。该 verdict 只接受“合同草案执行完成”，不接受 R8-0、真实资料、真实模型、真实应用或真实医学质量。

## Worker Outputs

- `worker_01`：定义逐项目 opaque identity、只读 A/B inventory、文件级证据、symlink/archive、重复与可变来源、零写入、隔离输出、manifest、撤销/重新准入和负向测试。
- `worker_02`：定义项目无关 extraction envelope、四类 payload、prompt/profile/binding/raw/parsed/coverage/source-anchor、独立 harness/LLM 职责及静态/动态防过拟合挑战。
- `worker_03`：定义真实应用/通知/§15.4、full/incremental、双角色双轮、P0-P4、缺陷传播、clean-streak reset 和 ego(lite) 的有序 gate。

三者均明确：未访问真实项目、未调用真实模型、未启动服务或浏览器、未修改产品源码或医学写作子系统、未声称最终接受。

## Manager Assessment

本 execution packet 按声明没有单独 manager。Codex 作为最终整合与接受主体完成了：

1. 统一状态语义，避免把存在、评估、执行和处置混成一个 `complete`；
2. 将来源准入、harness 责任、反过拟合、真实应用/通知/§15.4 串成不可跳过的 G0-G15；
3. 澄清 G1 只接受合同，G5 接受 synthetic readiness，G6 才允许 synthetic ego(lite)，G7 才首次允许逐项目来源访问；
4. 保留 MTPLX 长等待、显式 fallback、新 binding 和实际模型身份记录要求；
5. 保留 Codex 不得代替独立模型生成项目医学解构的硬边界；
6. 将项目根保持为 `P1..P5`，合同内不写入真实项目路径或项目专有医学常量。

## Codex Independent Verification

- 候选合同：`reviews/medical_monitoring_r8_gate0_source_admission_anti_overfit_contract_v0_1_20260831.md`
- 草案 SHA-256：`a19fd612c758f38107c937c93f44f1d693e3a68f6bea3f4200ee212d8a95158b`
- 文件规模：384 行、22046 bytes。
- 定向扫描未发现真实项目绝对路径、项目名、药物名、疾病名或用户已明确否定的临时 UI 术语。
- 三份 runner 报告均为单轮终态成功、无 timeout、无 fallback；真实模型/真实项目/浏览器仍未运行。
- 尚未完成 fresh-context 独立合同会商，因此文件保持 `DRAFT_FOR_INDEPENDENT_CHALLENGE`，不能冻结为 accepted。

## Cleanup Decision

保留 execution prompt、runner stdout 与 worker 报告，直到独立合同会商和摘要冻结完成；当前不清理，避免破坏审计链。接受后再使用 governed cleanup，而不是手工删除。
