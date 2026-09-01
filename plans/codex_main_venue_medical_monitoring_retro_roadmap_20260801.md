# Codex Main-Venue Plan: medical_monitoring_retro_roadmap_20260801

Date: 2026-08-01
Objective: 只读审查医学监查子系统需求、实现、测试、运行证据与中英文外部平台方法，形成需求-实现-证据差距矩阵、宏观及分阶段路线图、下一 Goal 文本和恢复 Prompt；不修改产品源码、不启动服务或真实项目。

## Task Decomposition

1. Re-anchor current global/project instructions, Goal state, and the v11 pause.
2. Read the full requirement and planning packet.
3. Inventory and inspect backend, frontend, APIs, repositories, shared contracts, and tests.
4. Verify English/Chinese platform, regulatory, standards, and eligible open-source evidence.
5. Produce the requirement-implementation-evidence gap analysis and architecture review.
6. Define macro, phase, and step objectives with entry/exit gates, dependencies, stop, and rollback rules.
7. Review the current Goal Prompt and write the next Goal objective plus recovery prompt.
8. Persist a detailed review and no-loss pause checkpoint; run the conference review gate.

## Source Packet

- `context/medical_monitoring_retro_roadmap_20260801_conference_context.md`
- Current v11 pause, terminal evidence, zero-submit evidence, Codex canary review, and active LOOP ledger.
- V1.1 manual, PRD gap matrix, P0-P10 implementation plan, current Goal Prompt, requirements traceability, and active task context.
- Monitoring implementation under `services/api/app/`, `frontend/src/`, and `tests/`.
- Current official/primary external sources verified by main Codex.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_codex_luna` | `codex` | `gpt-5.6-luna` | `runs/conference/medical_monitoring_retro_roadmap_20260801/general_codex_luna.md` |
| `general_pi_deepseek_flash` | `opencode-go` | `deepseek-v4-flash` | `runs/conference/medical_monitoring_retro_roadmap_20260801/general_pi_deepseek_flash.md` |

## Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_chair_pi_qwen38` | `alibaba` | `qwen3.8-max-preview` | `runs/conference/medical_monitoring_retro_roadmap_20260801/general_chair_pi_qwen38.md` |

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- Use the guard-generated hard waits. Do not poll or redispatch on latency.
- Record start/end, terminal state, session, fallback reason, and whether each output was incorporated.

## Codex Verification Checklist

- Product source and runtime libraries unchanged.
- 8911 and 5174 remain stopped; 18911 remains untouched.
- v9-v11 evidence remains frozen; no POST/provider/real-project execution occurred.
- Every material local claim has a file/section locator.
- Every material external claim has a current primary or official source.
- Open-source recommendations state an identifiable license; commercial products remain reference patterns only.
- P0-P10 status differentiates implementation from fresh runtime/release evidence.
- Roadmap has measurable exits and does not hide the v12 corrective or three-project release requirement.
- Both copyable prompts preserve current stop state and exact next safe action.
