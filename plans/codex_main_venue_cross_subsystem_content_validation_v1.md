# Codex Main-Venue Plan: cross_subsystem_content_validation_v1

Date: 2026-07-13
Objective: 统一入排、医学监查、TFL/PV与通用导入的文件技术可读性、内容一致性及充分告警后医学经理确认沿用契约；保留各子系统临床边界

## Task Decomposition

1. Audit each intake surface and separate technical readiness, content consistency, and downstream clinical gates.
2. Define a shared immutable decision model with module-specific check registries.
3. Implement the smallest reusable backend slice in generic source registration and active monitoring upload, then extend to registered eligibility/TFL/PV sources without inventing nonexistent upload UIs.
4. Verify match, mismatch, stale revision, partial acknowledgement, insufficient reason, and technical failure.
5. Run two-project real-source checks; any UI change requires a separate visual conference and desktop browser QC.

## Source Packet

See `context/cross_subsystem_content_validation_v1_conference_context.md` and the bounded source files listed there.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_aishuo_minimax` | `aishuo` | `MiniMax-M3` | `runs/conference/cross_subsystem_content_validation_v1/general_aishuo_minimax.md` |
| `general_buddy_deepseek` | `buddy` | `deepseek-v4-pro` | `runs/conference/cross_subsystem_content_validation_v1/general_buddy_deepseek.md` |
| `general_opencode_mimo` | `opencode-go` | `mimo-v2.5` | `runs/conference/cross_subsystem_content_validation_v1/general_opencode_mimo.md` |

## Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_chair_glm` | `buddy` | `glm-5.2` | `runs/conference/cross_subsystem_content_validation_v1/general_chair_glm.md` |

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

Record start/end time, pending/failed/incorporated status, retry reason, and whether late outputs were used.

## Codex Verification Checklist

- Confirm no security/malware scan semantics are reintroduced.
- Confirm override cannot change mismatch to match.
- Confirm technical failure is never overridable.
- Confirm stale decisions fail CAS and cannot silently carry forward.
- Confirm two different real projects and cross-module regression.
