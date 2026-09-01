# Codex Main-Venue Plan: mm_r7_phase_closure_review_20260831

Date: 2026-08-31
Objective: 独立审阅医学监查 R7 十项要求、System Design 15.1/15.4、Slice-01至09E的受限验收与当前源码边界；判断能否仅以 synthetic/offline engineering baseline 收口并进入 R8 合同冻结，还是必须先补本地通知或真实一键应用纵切；不得把真实项目、医学质量、真实安装或生产能力伪造成已完成。

## Task Decomposition

1. Reconcile the ten R7 plan steps to accepted slices and current source.
2. Test the proposed narrow phase label against the stronger System Design 15.1/15.4 wording.
3. Decide whether disabled notification center / lack of an off-page completion notice blocks R7.
4. Decide whether a CLI management shell without complete runtime dependencies or desktop launcher blocks R7.
5. If R7 may close, define explicit R8 source-admission, anti-overfitting, real backup/migration and real-app gates; otherwise define the smallest final R7 slice.

## Source Packet

The authoritative list is in the conference context. Historical test counts are supporting evidence only; current files and acceptance boundaries control.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_single_object` | `cms-router` | `minimax-m3` | `runs/conference/mm_r7_phase_closure_review_20260831/general_single_object.md` |

## Conference Panel Coordination

- Preferred browser advisory chair: `chatgpt-web-pro-advisory` via `codex-with-chatgpt` (`Pro` / `GPT-5.6 Sol`). Codex remains the formal packet chair and final authority; the browser role is not dispatched through the runner.
- No sub-venue chair. Codex leads the assigned panel directly.

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- Initialized 2026-08-31 10:43 CST. Use one runner-owned hard wait and same-session follow-up only if Codex identifies a concrete omission.

## Codex Verification Checklist

- [ ] Ten R7 steps reconciled without expanding limited slice claims
- [ ] Local notification meaning resolved from source and user experience
- [ ] No-manual-service/local-app claim resolved against actual deploy contents
- [ ] System Design 15.4 real-validation obligation placed in a concrete gate
- [ ] Phase label cannot be mistaken for real-project, production or commercial acceptance
- [ ] R8 cannot read real projects before accepted source-admission/anti-overfit contract
