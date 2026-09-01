# Codex Main-Venue Plan: medical_monitoring_r5_s4_20260819

Date: 2026-08-19
Objective: 先冻结 R5-S4 Risk Inspector 与多模型证据归并的 synthetic/offline、renderer-neutral 实施合同；合同独立接受前不实现 runtime。

## Task Decomposition

1. 锚定 System Design、R0–R8、R5 总合同、exact contract、R4 ensemble/D10 与已接受 S2/S3。
2. Participant 1 独立设计 exact schema、authority mapping、invariants、challenge artifacts 与写入边界。
3. Participant 2 从对抗视角审查 0/1/N、身份/版本/来源/哈希、冲突可见性、裁决独立性、中文用户投影和禁止分支。
4. Codex 合并两路证据，形成最小 S4 合同源与可机械验证工件；不实现 runtime。
5. fresh isolated reviewer 仅对稳定 SHA 返回 `ACCEPT_R5_S4_CONTRACT` 或 `REVISE_R5_S4_CONTRACT`；按同一 reviewer 会话闭环缺口。
6. 仅在合同接受后另立 S4 runtime 三项工作和独立验收。

## Source Packet

- Authority：R4 `ReferenceBaselineItem/BaselineAssessment/AnalysisAttempt/WorkerAnalysisOutput/EvidenceVerification/ConflictVisibility/AdjudicationBinding`、ensemble runtime，以及 D10 `ModelEvidence`/risk/query/source public projection。
- Accepted R5 anchors：S2 thin-slice Inspector binding 与 S3 current-risk/center/cockpit authority；不得修改其冻结 SHA。
- Required user projection：风险标题/域/等级/当前变化/受试者中心；依据+发现+建议核实；正反证；基座和独立分析；确定性核对与独立裁决；事实/listing/方案/IB/知识；Query/历史；Subject Journey 深链。
- Required cases：0/1/N、baseline confirmed/partial/unsupported/outdated/insufficient/not-applicable、single addition、graded conflict、mutual negation、baseline miss、verification failure、independent adjudication、高风险持续可见、缺失/hidden/source unavailable。

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_pi_qwen38` | `alibaba` | `qwen3.8-max` | `runs/conference/medical_monitoring_r5_s4_20260819/general_pi_qwen38.md` |
| `general_grok46` | `grok-build` | `grok-4.6` | `runs/conference/medical_monitoring_r5_s4_20260819/general_grok46.md` |

## Conference Panel Coordination

- No sub-venue chair. Codex leads the assigned panel directly.

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- 每路一次完整首轮，最多 120 分钟 hard wait；慢响应保持 pending。
- 仅对明确 actionable gap 使用同一 session follow-up；不因日夜路由切换废弃 session。
- 记录 provider/model/session/pass/terminal state/fallback reason；仅终态失败才启用声明 fallback。

## Codex Verification Checklist

- [ ] 两路 prompt preflight 与 conference route validation 通过。
- [ ] participant 输出完整、彼此独立、边界合规。
- [ ] exact schema/mapping/invariants/challenge registry 不是 prose-only 或 self-proof。
- [ ] generator `--check`、normal/O2 verifier、focused tests、Ruff/compile 通过。
- [ ] source pins、artifact exact set、首尾 SHA 与 tamper probes 通过。
- [ ] R4 与 R5 S1–S3 接受 SHA 不变；医学写作/前端/服务未触碰。
- [ ] 8911 IPv4/IPv6 均未监听。
- [ ] fresh independent reviewer 返回 `ACCEPT_R5_S4_CONTRACT`。
