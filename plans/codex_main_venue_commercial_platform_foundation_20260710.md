# Codex Main-Venue Plan: commercial_platform_foundation_20260710

Date: 2026-07-10
Objective: 为康哲AI医学经理工作台确定并落地共享事务持久化、独立AI执行治理、审计与私有化迁移边界，作为六个医学子系统商业化的共同底座

## Task Decomposition

1. Recheck current persistence and AI-runtime behavior against the latest canonical-project code, not the stale pre-canonical audit.
2. Record current regulatory, commercial-platform, database, durable-workflow, authorization, and observability evidence with adoption/rejection reasons.
3. Obtain independent architecture passes from qwen3.7-plus, mimo-v2.5, Reasonix deepseek-flash, Buddy minimax-m3, and Buddy GLM-5.2; use at least three completed outputs for the decision.
4. Have the Hermes minimax chair compare participant disagreements and produce a bounded recommendation.
5. Have Reasonix deepseek-pro review the main-venue package and the Chinese clinical/approval terminology in the proposed contracts.
6. Codex writes the accepted design and implementation plan, then executes TDD in narrow tasks:
   - shared write-envelope contracts;
   - SQLite schema/migration and transaction Unit of Work;
   - idempotency and optimistic-concurrency error mapping;
   - append-only audit integrity metadata and diagnostics;
   - first compatibility adapters for approval/inbox and AI runs;
   - project-scoped AI policy resolution and source allowlists.
7. Run focused tests first, then full backend regression, frontend contract/build checks, restart/fault/collision tests, and public-payload scans.
8. Request independent code review, fix all Critical/Important findings, rerun tests, and update system/subsystem logs.

Implementation is not authorized from a model suggestion alone. Codex must verify code, tests, and current runtime behavior before each production write.

## Source Packet

- `context/commercial_platform_foundation_20260710_conference_context.md`
- `records/active_slices/commercial_platform_foundation_20260710/COMMERCIAL_REQUIREMENTS_TRACEABILITY_MATRIX.md`
- `records/active_slices/commercial_platform_foundation_20260710/RESEARCH_AND_DECISION_LOG.md`
- `records/soft_pause_20260710_0945_canonical_project_context/*`
- `records/soft_pause_20260709_1105_lossless_full_backup/USER_REQUIREMENTS_FULL_LEDGER.md`
- `records/soft_pause_20260709_1105_lossless_full_backup/CROSS_PROJECT_GENERALIZATION_TEST_GATE.md`
- `runs/subagents/20260710_commercialization_baseline/architecture_generalization_audit.md`
- Current persistence/AI code and relevant tests listed in the conference context.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `participant_qwen_plus` | `opencode-go` | `qwen3.7-plus` | `runs/conference/commercial_platform_foundation_20260710/participant_qwen_plus.md` |
| `participant_mimo` | `opencode-go` | `mimo-v2.5` | `runs/conference/commercial_platform_foundation_20260710/participant_mimo.md` |
| `participant_ds_flash` | `reasonix-cli` | `deepseek-v4-flash` | `runs/conference/commercial_platform_foundation_20260710/participant_ds_flash.md` |
| `participant_buddy_minimax` | `buddy` | `minimax-m3` | `runs/conference/commercial_platform_foundation_20260710/participant_buddy_minimax.md` |
| `participant_glm52_product` | `buddy` | `glm-5.2` | `runs/conference/commercial_platform_foundation_20260710/participant_glm52_product.md` |

## Hermes Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `hermes_lead` | `opencode-go` | `minimax-m3` | `runs/conference/commercial_platform_foundation_20260710/hermes_lead.md` |

## Main-Venue DeepSeek Pro Review

- Agent/model: Reasonix CLI `deepseek-pro` alias for `deepseek-v4-pro`.
- Reasoning: maximum configured Reasonix effort. Verify stdout/metrics when possible.
- Forbidden: Hermes, OpenCode Go, Hermes custom providers, or direct DeepSeek provider `deepseek-v4-pro` for this main-venue high-risk review.
- Output: `runs/conference/commercial_platform_foundation_20260710/main_deepseek_pro.md`

## Timeout And Retry Tracking

- Record start/end time, provider/model initialization marker, API completion, usage, pending/failed/incorporated status, retry reason, and whether late outputs were used.
- Do not mark slow routes failed before the conference timeout policy and one controlled retry.
- Buddy failures use the user-approved qwen3.7-plus/mimo-v2.5 fallback without deleting failure evidence.
- DeepSeek V4 remains Reasonix-only under the current project route rule.

## Codex Verification Checklist

- [ ] Current code evidence and participant prompts contain no stale `TODO` or unbounded read/write permission.
- [ ] At least three independent participant outputs completed and were compared.
- [ ] Architecture benefit/risk/rejection record is explicit.
- [ ] Shared contracts have failing-first tests before implementation.
- [ ] SQLite transaction tests cover rollback, restart, collision, replay, stale version, and corruption diagnosis.
- [ ] AI policy tests cover project/task/data-classification allow, blocked, retry, validation, and public redaction paths.
- [ ] Existing approval/inbox/AI behavior remains regression-safe during compatibility migration.
- [ ] Full backend tests and frontend build/contract tests pass with fresh logs.
- [ ] Codex code review and Reasonix deepseek-pro review are complete; no unresolved Critical/Important finding remains in this slice.
- [ ] System and affected subsystem logs are updated.
