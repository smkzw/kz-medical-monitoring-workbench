# Codex Main-Venue Plan: medical_monitoring_r2_c_acceptance_20260810

Date: 2026-08-10
Objective: 独立审阅并验收冻结的 R2-C 功能性持久化、重开、幂等、发布读取一致性、R1 只读适配与迁移回滚实现；仅报告可复现缺陷并给出 ACCEPT/VETO

## Task Decomposition

1. Freeze and hash the current R2-C snapshot.
2. Run fresh-context contradiction review against persistence/migration contracts.
3. Reproduce each VETO locally, apply bounded functional repair, and rerun focused/full regression.
4. Exhaust same-session recovery before declared fallback.
5. Freeze ACCEPT evidence and transition to R3.

## Source Packet

- `worker_03.md` acceptance contract.
- R2-C source and tests.
- Frozen digest and R1 read-only digest.
- Luna VETO reports and Pi final acceptance report.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `independent_codex_luna` | `codex` | `gpt-5.6-luna` max (CLI compatibility) | `runs/conference/medical_monitoring_r2_c_acceptance_20260810/independent_codex_luna_round3.md` |
| `independent_pi_final` | `cms-smk` | `cms-model` high | `runs/conference/medical_monitoring_r2_c_acceptance_20260810/independent_pi_final.md` |

## Conference Panel Coordination

- No sub-venue chair. Codex leads the assigned panel directly.

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- Luna: one initial pass plus two same-session repair follow-ups; all completed normally, no latency fallback.
- Pi/CMS: used only after Luna recovery passes were exhausted and acceptance still failed; one pass, completed normally, no lower fallback.

## Codex Verification Checklist

- [x] R2-C focused tests: 105 passed.
- [x] Full R2 tests: 598 passed.
- [x] In-memory compile: 33 Python files.
- [x] R1 digest unchanged.
- [x] No cache and no 8911 listener.
- [x] Durable acceptance record written.
