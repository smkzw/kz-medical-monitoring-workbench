# Codex Main-Venue Plan: mm_r6_runtime_slice_03_acceptance_20260827

Date: 2026-08-27 to 2026-08-28
Objective: 独立审阅 R6 第三纵切 synthetic/offline ReportReviewBundle 实现是否满足 context/medical_monitoring_r6_runtime_slice_03_contract_20260827.md 与权威合同 §7/contract.json。重点寻找内容寻址、三件身份与 issue/evidence/locator 共享、annotation/anchor map 一致性、DRAFT 未决项保留、IssueTransition/revision diff 的失败开放；核对 360 回归与 9 宫格证据。不得修改文件，不得接受产品/真实报告/医学/渲染范围。给出可执行缺陷或明确的条件接受结论。

## Task Decomposition

1. 核对权威 §7/contract.json 与 slice-03 合同边界。
2. 独立审阅三件 identity、内容寻址、anchor map、DRAFT 未决项和 revision diff。
3. 对失败开放进行同会话纠偏复核。
4. Codex 跑 focused/full/normal-`-O`-`-OO` × hash-seed 九宫格并同步 receipt。
5. 仅以 synthetic/offline JSON 范围作出最终验收。

## Source Packet

- `context/medical_monitoring_r6_runtime_slice_03_contract_20260827.md`
- `reviews/medical_monitoring_r6_external_report_mode_output_contract_v0_1_20260827.md`
- `artifacts/medical_monitoring_r6_external_report_mode_output_contract_v0_1/contract.json`
- slice-01/02 frozen receipts and adjacent tests
- current slice-03 implementation/tests/receipt

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_pi_antigravity` | `google-antigravity` | `gemini-3.7-flash` | `runs/conference/mm_r6_runtime_slice_03_acceptance_20260827/general_pi_antigravity.md` |
| `general_grok46` | `grok-build` | `grok-4.6` | `runs/conference/mm_r6_runtime_slice_03_acceptance_20260827/general_grok46.md` |

## Conference Panel Coordination

- No sub-venue chair. Codex leads the assigned panel directly.

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- 两个主参与者均终态成功，无 fallback、无 timeout。
- Gemini：1 pass，149.424 s，结果纳入架构核对；其早期计数不覆盖最终字节。
- Grok Build：保持 session `339bd17d-bf5c-468e-9908-7cb30c00346c`，按缺陷定向续跑；当前 durable runner log 的最后两轮共 199.631 s，均纳入，未新开 session。
- 慢响应按 120 分钟 hard-wait 处理，未作固定间隔重派。

## Codex Verification Checklist

- [x] sidecar-only，无伪造 `in_place_copy`
- [x] 18 字段 identity 与内容 ID 可重算
- [x] annotation issue/evidence/locator 与 matrix 权威一致
- [x] page/order/ordinal-only locator 不可冒充 verified anchor
- [x] DRAFT 保留 unresolved/conflict/not-evaluable/gaps
- [x] lifecycle/evidence-only resolution 不得成为 resolved
- [x] omitted-unit/claim relink 不得关闭原缺口
- [x] merge/split 对所有 source-target 组合失败闭合
- [x] positive open-to-claimed resolution 保持可用
- [x] focused 71；full 377；九宫格 9/9 每格 71
- [x] 医学写作 aggregate 542 / `feef0f...` 保持
- [x] 8911/5174 停止；未使用真实项目
