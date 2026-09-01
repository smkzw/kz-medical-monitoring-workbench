# Codex Main-Venue Plan: monitoring_my009_fullchain_20260710

Date: 2026-07-10
Objective: Design and implement a reusable two-real-project medical-monitoring chain for RUX-03-002 and MY009-UC from original listing and protocol, including subject catalog, subject timeline, patient profile, risk inbox, incremental batch boundaries, privacy, independent-AI prompts, desktop interactions, and cross-project fail-closed tests.

## Task Decomposition

1. Confirm current RUX and MY009 route/data boundaries and classify real source snapshots.
2. Compare commercial/open-source monitoring patterns against user constraints and ICH E6(R3).
3. Decide the smallest reusable adapter/registry contract without rewriting the verified RUX service.
4. Add failing tests for MY009 canonical/alias routing, 26-subject catalog, five anchor subjects, event-domain boundaries, trends, privacy and no demo/RUX fallback.
5. Implement the MY009 adapter and route registry; keep medical interpretation fail-closed.
6. Add project-scoped risk/inbox projection only for verified deterministic findings.
7. Add snapshot identity and explicit first-batch/no-baseline semantics; then exercise a real historical batch pair if source classification remains acceptable.
8. Run API, full backend, production build and 1600x1000 browser QC across RUX and MY009.
9. Record accepted decisions, rejected alternatives, defects and remaining commercial boundaries.

## Source Packet

- `context/monitoring_my009_fullchain_20260710_conference_context.md`
- `records/active_slices/monitoring_my009_fullchain_20260710/SOURCE_AUDIT.md`
- `records/research/medical_monitoring_external_benchmark_20260710.md`
- Current code and test files enumerated in the conference context.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `participant_qwen_plus` | `opencode-go` | `qwen3.7-plus` | `runs/conference/monitoring_my009_fullchain_20260710/participant_qwen_plus.md` |
| `participant_mimo` | `opencode-go` | `mimo-v2.5` | `runs/conference/monitoring_my009_fullchain_20260710/participant_mimo.md` |
| `participant_ds_flash` | `reasonix-cli` | `deepseek-v4-flash` | `runs/conference/monitoring_my009_fullchain_20260710/participant_ds_flash.md` |

## Hermes Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `hermes_lead` | `opencode-go` | `minimax-m3` | `runs/conference/monitoring_my009_fullchain_20260710/hermes_lead.md` |

## Main-Venue DeepSeek Pro Review

- Agent/model: Reasonix CLI `deepseek-pro` alias for `deepseek-v4-pro`.
- Reasoning: maximum configured Reasonix effort. Verify stdout/metrics when possible.
- Forbidden: Hermes, OpenCode Go, Hermes custom providers, or direct DeepSeek provider `deepseek-v4-pro` for this main-venue high-risk review.
- Output: `runs/conference/monitoring_my009_fullchain_20260710/main_deepseek_pro.md`

## Timeout And Retry Tracking

- Record each participant's start/end, terminal state, actual provider/model marker, file-write result and incorporation decision in `metrics/monitoring_my009_fullchain_20260710_conference_metrics.md`.
- Qwen and MiMo run independently in Hermes; DeepSeek Flash runs only through Reasonix. Rate-limited OpenCode routes retry serially once.
- Chair runs only after all available participant files are present or explicitly recorded pending.

## Codex Verification Checklist

- [ ] Participant prompts pass guard preflight and write exactly one bounded output.
- [ ] No participant treats prior derived HTML/risk summaries as source data.
- [ ] Adapter decision preserves canonical project isolation and CM/IP boundary.
- [ ] TDD red tests prove MY009 currently has zero monitoring subjects/inbox before implementation.
- [ ] Five real MY009 subjects exercise each available domain and trend path.
- [ ] RUX anchor tests remain unchanged and pass.
- [ ] Browser screenshots use fixed 1600x1000 viewport and actual project switching.
- [ ] Full suite and build pass; final report records all remaining boundaries.
