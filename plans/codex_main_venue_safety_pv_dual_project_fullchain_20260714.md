# Codex Main-Venue Plan: safety_pv_dual_project_fullchain_20260714

Date: 2026-07-14
Objective: 补齐RUX与MY009双项目Safety/PV五类医学复核、统一SQLite幂等/CAS/审计、来源换版失效、医学监查交接和桌面端完整交互

## Task Decomposition

1. Audit the current JSONL review store, five action semantics, source admission and monitoring projection.
2. Define the smallest explicit state machine and SQLite event/state contract with idempotency, CAS and runtime audit.
3. Add failing two-project tests before production changes.
4. Implement backend storage/service/API changes without duplicating monitoring risks.
5. Refine the desktop review interaction only where the full-chain tests expose a concrete gap.
6. Run real RUX and MY009 API/button/source-drift/cold-restart loops, then visual panel review and Codex acceptance.

## Source Packet

Read the conference context and the exact bounded code/test files named there. Treat manifest-derived source facts as evidence; do not open or edit clinical source files. Every participant must separate current fact, inference, recommendation and uncertainty.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_aishuo_minimax` | `aishuo` | `MiniMax-M3` | `runs/conference/safety_pv_dual_project_fullchain_20260714/general_aishuo_minimax.md` |
| `general_buddy_deepseek` | `buddy` | `deepseek-v4-pro` | `runs/conference/safety_pv_dual_project_fullchain_20260714/general_buddy_deepseek.md` |
| `general_opencode_mimo` | `opencode-go` | `mimo-v2.5` | `runs/conference/safety_pv_dual_project_fullchain_20260714/general_opencode_mimo.md` |

## Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_chair_glm` | `buddy` | `glm-5.2` | `runs/conference/safety_pv_dual_project_fullchain_20260714/general_chair_glm.md` |

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- Initialized 2026-07-14 11:51 CST.
- Participant and chair status will be recorded in the conference metrics and task record.

## Codex Verification Checklist

- Two real projects and all five actions.
- Invalid transition, empty comment, duplicate request, changed payload under same key, stale expected revision, cold restart and source drift.
- Monitoring collaboration creates no duplicate risk identity or second disposition state.
- Handoff and inbox appear and disappear with the current action/revision.
- SQLite schema migration backup, integrity, foreign keys, immutable records and audit chain.
- 2048x1024 and 1920x1080 desktop interaction and visual QC.
- Focused tests, frontend build and full repository regression.
