# Codex Main-Venue Plan: mm_r7_slice08d_contract_20260830

Date: 2026-08-30
Objective: 独立挑战并冻结R7 Slice-08D三模式synthetic综合回归合同，核对三模式语义、确定性、故障恢复、相邻回归、用户中文边界和P0-P4完成门；不修改产品、不启动服务/真实项目/模型、不触碰医学写作

## Task Decomposition

1. Compare v0.1 against the frozen Slice-08 v0.2 semantics and accepted 08A/08B/08C boundaries.
2. Challenge all four synthetic scenarios, seven change kinds, publication/continuity atomicity, hash-seed/optimization determinism, and failure recovery.
3. Verify the oracle is independent and does not consume product output, fixture names, case IDs, or expected hashes as decisions.
4. Review user-visible Chinese and public-schema boundaries without adding UI work.
5. Revise only the contract when required; freeze only after independent ACCEPT and Codex source review.

## Source Packet

- `reviews/medical_monitoring_r7_slice08d_three_mode_regression_contract_v0_1_20260830.md`
- frozen Slice-08 v0.2 contract and 08A/08B/08C acceptance records
- current continuity/bridge/registry source and directly related tests

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_single_object` | `cms-router` | `minimax-m3` | `runs/conference/mm_r7_slice08d_contract_20260830/general_single_object.md` |

## Conference Panel Coordination

- No sub-venue chair. Codex leads the assigned panel directly.

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- Primary route completed twice in the same session; no fallback or route substitution.
- Provider/model: `cms-router/minimax-m3:xhigh`.
- Session: `01a05041-e2e9-7000-ac7a-cf423c750dd2`.
- Round 1: 51.017 s; verdict `ACCEPT_WITH_REQUIRED_REVISIONS_v0_2`.
- Round 2: 29.410 s; verdict `ACCEPT_CONTRACT_V0_2`.
- The correction was applied only to the contract. No product, service, browser, model harness, real project, or medical-writing surface was changed.

## Codex Verification Checklist

- [x] Participant reads v0.1 and frozen sources, not summaries alone.
- [x] Twenty-cell scenario matrix and reverse mode/basis assertions have no missing acceptance cell.
- [x] Independent oracle and anti-overfit boundary are executable as a contract.
- [x] Fault/recovery and public Chinese boundaries are precise.
- [x] P0-P4 and completion gate are unambiguous.
- [x] Codex accepts and freezes v0.2 as an additive appendix to v0.1.
