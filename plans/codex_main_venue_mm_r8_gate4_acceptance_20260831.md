# Codex Main-Venue Plan: mm_r8_gate4_acceptance_20260831

Date: 2026-08-31
Objective: 独立审阅医学监查子系统R8 G4合成通知seam与System Design 15.4十三项程序，核查合同符合性、失败关闭、确定性、反过拟合、发布边界及P0-P4；不得写代码、启动服务/浏览器/模型或读取真实项目

## Task Decomposition

1. Independently inspect the frozen G3/G4/anti-overfit contracts and current implementation.
2. Trace notification facts, outbox/channel evidence, persistent fallback and navigation gates.
3. Trace each of the 13 §15.4 rows to a reused R7 primitive and concrete assertion.
4. Challenge deterministic replay, path containment, release inventory and anti-overfit claims.
5. Return P0-P4 findings and a disposition; do not edit files.

## Source Packet

The authoritative source packet is enumerated in
`context/mm_r8_gate4_acceptance_20260831_conference_context.md`. Worker reports and runner logs
are deliberately excluded to preserve verifier isolation.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_single_object` | `cms-router` | `minimax-m3` | `runs/conference/mm_r8_gate4_acceptance_20260831/general_single_object.md` |

## Conference Panel Coordination

- Preferred browser advisory chair: `chatgpt-web-pro-advisory` via `codex-with-chatgpt` (`Pro` / `GPT-5.6 Sol`). Codex remains the formal packet chair and final authority; the browser role is not dispatched through the runner.
- No sub-venue chair. Codex leads the assigned panel directly.

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

Record runner start/end, route/session identity, terminal or pending state, fallback/recovery reason,
and whether the output was incorporated.

## Codex Verification Checklist

- [ ] Participant did not modify source or cross forbidden boundaries.
- [ ] Every P0-P4 finding is traced to current code/contract evidence.
- [ ] P0/P1 are closed before acceptance.
- [ ] 67 focused and 196 adjacent checks remain green after any remediation.
- [ ] 9-way digest determinism remains identical.
- [ ] Release manifest and medical-writing fingerprint are remeasured.
- [ ] 8911/5174/8984 remain stopped.
