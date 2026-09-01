# Codex Main-Venue Plan: mm_r7_slice08c4_visual_contract_20260830

Date: 2026-08-30
Objective: 独立只读挑战并验收R7 Slice-08C-4 ego(lite)三视口运行时与视觉专项合同；核对用户任务、参考图并列比较、overlay/push、真实焦点、数据对账、中文视觉质量、全部P0-P4清零和隔离运行边界，关闭P0-P2后才允许启动隔离服务

## Task Decomposition

1. 只读核对 08C-4 草案、08C-1/2/3 冻结合同、当前产品源码、旧结构截图与用户流向参考。
2. 同一独立会话逐轮挑战合同；Codex 只修改合同、fixture 规格与冻结参考，不启动运行时。
3. 关闭 reference/fixture/中文闭集/overlay-push/数据对账/P 级别与身份路由缺口。
4. 独立会话给出 `ACCEPT_CONTRACT` 后，Codex 冻结合同并完成治理验证；运行时视觉接受留给独立 visual execution + visual conference。

## Source Packet

- `context/medical_monitoring_r7_slice08c4_ego_visual_acceptance_contract_20260830.md`
- `context/medical_monitoring_r7_slice08c4_synthetic_fixture_spec_20260830.md`
- `context/mm_r7_slice08c4_visual_contract_20260830_conference_context.md`
- 08C v0.1/v0.2 与 08C-3 合同/接受记录
- 当前 R7 product API、projection、Journey drawer/Page/CSS
- 工作区冻结 Sankey 与 07C-4/R5 结构参考截图

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `visual_single_object` | `grok-build` → declared `cursor` fallback | `grok-4.6` → `cursor-grok-4.6` | initial + same-session rounds 2–4 under `runs/conference/mm_r7_slice08c4_visual_contract_20260830/` |

## Conference Panel Coordination

- No sub-venue chair. Codex leads the assigned panel directly.

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- Primary Grok Build ended before a resumable session; runner used the declared Pi/Cursor fallback.
- Cursor fallback session `01a04e7f-cf8d-7000-add5-eaa9e19738a1` was preserved through four review rounds.
- No timeout was classified from latency; no late output or re-dispatch occurred.
- Round 1 `REVISE`; Round 2/3 narrowed residual identity-route gaps; Round 4 `ACCEPT_CONTRACT`.

## Codex Verification Checklist

- [x] Contract/spec/reference all on disk.
- [x] P0/P1/P2 zero in same-session independent Round 4.
- [x] 8911/5174/8984 stayed stopped; no ego(lite) or real project/model run.
- [x] Contract acceptance not mislabeled runtime visual acceptance.
- [x] Next action is governed visual execution, then separate visual conference.
