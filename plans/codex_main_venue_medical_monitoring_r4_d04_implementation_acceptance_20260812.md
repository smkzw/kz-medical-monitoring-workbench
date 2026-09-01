# Codex Main-Venue Plan: medical_monitoring_r4_d04_implementation_acceptance_20260812

Date: 2026-08-12
Objective: 对冻结的R4 D04实现快照进行独立医学方案语义与工程确定性双角色会商验收

## Task Decomposition

1. Freeze the accepted 13-path contract/implementation snapshot and prohibit edits during review.
2. Run a fresh-context medical/protocol-semantics reviewer over the full D04 vertical slice.
3. In parallel, run a fresh-context engineering/determinism reviewer over the same snapshot.
4. Codex verifies reviewer evidence, reconciles only objective conflicts, reruns decisive checks and either rejects with a targeted same-session repair or accepts the snapshot.
5. On acceptance, fill review/metrics, pass the conference review gate, archive execution/conference evidence and update the durable R4 roadmap/LOOP checkpoint.

## Source Packet

- `reviews/medical_monitoring_r4_d04_protocol_pd_slice_contract_v1_20260812.md`
- `context/medical_monitoring_r4_d04_implementation_snapshot_20260812.md`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/{contracts,lifecycle,protocol,protocol_projection,protocol_fixtures}.py`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/__init__.py`
- `poc/medical_monitoring_ai_native_r4/tests/test_{shared_domain_protocol,lifecycle_projection,protocol_slice,protocol_projection,protocol_challenge_matrix}.py`
- `poc/medical_monitoring_ai_native_r4/README.md`

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_pi_qwen38` | `alibaba` | `qwen3.8-max` | `runs/conference/medical_monitoring_r4_d04_implementation_acceptance_20260812/general_pi_qwen38.md` |
| `general_grok45` | `grok-build` | `grok-4.5` | `runs/conference/medical_monitoring_r4_d04_implementation_acceptance_20260812/general_grok45.md` |

## Conference Panel Coordination

- No sub-venue chair. Codex leads the assigned panel directly.

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- Both roles launch once in parallel and remain pending until terminal result or 120-minute hard wait.
- Follow-ups, if needed, reuse the same provider session. No fixed-interval redispatch and no fallback for latency alone.
- Codex records declared/effective route, session id, fallback reason if any and whether each output was incorporated.

## Codex Verification Checklist

- Pre/post snapshot hashes match.
- Both participant reports are independent, evidence-bearing and terminal.
- Contract SHA unchanged; R4/R2/R3/focused tests, Ruff and compileall pass; 8911 stopped.
- No implementation/test edits occurred during conference.
- Every blocking reviewer finding is either reproduced and repaired or disproved with direct evidence before acceptance.
- Review and metrics files are complete enough for `review-gate --require-verification`.
