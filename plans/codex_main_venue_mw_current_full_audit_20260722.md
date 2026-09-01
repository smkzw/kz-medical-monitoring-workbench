# Codex Main-Venue Plan: mw_current_full_audit_20260722

Date: 2026-07-22
Objective: 从资深医学撰写用户、产品、临床科学、后端、前端、独立AI与DOCX成品视角审计当前医学写作子系统，输出可复现差距和修复优先级

## Task Decomposition

1. Qoder/Qwen3.8 current-source audit with reproducible technical evidence.
2. Kimi k3(high) independent audit emphasizing a lazy but expert medical writer and frontend/backend journey coherence.
3. Codex compares reports with current files/tests, reproduces accepted findings, rejects stale or unsupported claims, and feeds only verified items into the repair queue.
4. Repairs remain serialized by shared write surface; current Pauli/Mendel agents finish before overlapping frontend/repository work begins.

## Source Packet

- `context/mw_current_full_audit_20260722_conference_context.md`
- Current rebaseline records named there.
- Current `frontend-v2/src/App.jsx`, `frontend-v2/src/styles.css`, services, contracts and tests discovered from the audited path.
- Historical audit only as a regression checklist, not current truth.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_aishuo_cms` | `aishuo` | `cms-model` | `runs/conference/mw_current_full_audit_20260722/general_aishuo_cms.md` |
| `general_opencode_deepseek_flash` | `opencode-go` | `deepseek-v4-flash` | `runs/conference/mw_current_full_audit_20260722/general_opencode_deepseek_flash.md` |

## Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_chair_grok45` | `grok-build` | `grok-4.5` | `runs/conference/mw_current_full_audit_20260722/general_chair_grok45.md` |

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- Qoder existing interactive process: `qodercli`, model must be `Qwen3.8-Max-Preview`; one complete prompt, no status turns.
- Kimi existing interactive process: `kimi`, model `kimi-code/k3`, reasoning `high`; one complete prompt, no status turns.
- Check completion only by terminal/session log and report completion marker at coarse intervals. Same-session follow-up only for a concrete missing artifact or contradictory evidence.

## Codex Verification Checklist

- Reproduce every adopted P0/P1.
- Cross-check current source dates/paths to reject stale `qoderwork` evidence.
- Run focused backend/frontend tests for adopted findings.
- Browser and Word claims remain unaccepted until Codex observes the real audience runtime.
- Update durable gap matrix and task record with accepted/rejected findings and evidence.
