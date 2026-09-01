# Codex Main-Venue Plan: mw_search_contract_v4_20260715

Date: 2026-07-15
Objective: 复核医学写作竞品注册库检索合同v4：旧记录迁移、RA/CRSwNP跨项目适配、实际过滤条件与医学分诊分层、快照一致性及只读桌面可读性

## Task Decomposition

1. Inspect the contract/migration for data preservation and fail-closed invariants.
2. Trace actual registry request construction and prove triage-only values cannot leak into it.
3. Challenge RA/CRSwNP cross-project coverage and phase normalization edge cases.
4. Inspect frontend source and supplied screenshot/report for truthfulness, density, readability and contradictory states.
5. Rank any findings by production impact; Codex verifies and decides whether changes are required.

## Source Packet

Use only the files enumerated in the conference context plus `/Users/smkzw/.hermes/SOUL.md` for Hermes roles. The screenshot and JSON are evidence; no role may claim final visual acceptance. Stable runtime is read-only and must not be contacted.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_aishuo_minimax` | `aishuo` | `MiniMax-M3` | `runs/conference/mw_search_contract_v4_20260715/general_aishuo_minimax.md` |
| `general_opencode_deepseek_flash` | `opencode-go` | `deepseek-v4-flash` | `runs/conference/mw_search_contract_v4_20260715/general_opencode_deepseek_flash.md` |

## Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_chair_grok45` | `grok-build` | `grok-4.5` | `runs/conference/mw_search_contract_v4_20260715/general_chair_grok45.md` |

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- One complete pass per role. Follow-up only if Codex finds a concrete evidence gap or contradiction.
- Participant soft wait 20 minutes; chair hard wait 90 minutes. Slow remains pending under the configured failure rule.

## Codex Verification Checklist

- Reproduce each claimed issue against current source or stable read-only API.
- Reject suggestions that broaden search semantics without an explicit registry-filter contract.
- Preserve plan/snapshot/corpus identifiers and avoid hidden migration writes.
- Keep Codex as final authority for screenshot, stable runtime and production acceptance.
