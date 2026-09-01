# Codex Main-Venue Plan: rux_approval_persistence_20260709

Date: 2026-07-09
Objective: Harden RUX medical-monitoring internal approval so ApprovalGate and approval actions persist across backend restart without changing clinical boundaries or leaking local source paths.

## Task Decomposition

1. Baseline context and external principle check.
   - Done when current handoff, storage implementation, and relevant tests are read.
   - Verification: notes in conference context and local logs.
2. TDD red tests for restart recovery.
   - Add tests that fail because RUX approval gates/actions are memory-only.
   - Verification: focused tests fail for the expected missing persistence reason.
3. Minimal persistent store implementation.
   - Prefer append-only JSONL event store matching existing runtime style.
   - Recover RUX approval gates and decisions for virtual RUX project without changing generic demo behavior.
   - Verification: red tests turn green.
4. Surface and boundary verification.
   - Focused tests for workbench inbox, approval center, frontend contract.
   - Browser/API QC if public payload or frontend behavior changes.
5. Records and review closure.
   - Update subsystem logs, conference review/metrics, and next-risk list.

## Source Packet

- `records/soft_pause_20260709_lossless_handoff/*`
- `services/api/app/demo_repository.py`
- `services/api/app/workbench_inbox.py`
- `services/api/app/main.py`
- `packages/contracts/workbench_contracts/models.py`
- `tests/test_approval_center.py`
- `tests/test_workbench_inbox.py`
- `tests/test_frontend_monitoring_contract.py`
- `frontend/tests/rux_monitoring_inbox_qc.mjs`

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `participant_qwen_plus` | `opencode-go` | `qwen3.7-plus` | `runs/conference/rux_approval_persistence_20260709/participant_qwen_plus.md` |
| `participant_mimo` | `opencode-go` | `mimo-v2.5` | `runs/conference/rux_approval_persistence_20260709/participant_mimo.md` |
| `participant_ds_flash` | `deepseek` | `deepseek-v4-flash` | `runs/conference/rux_approval_persistence_20260709/participant_ds_flash.md` |

## Hermes Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `hermes_lead` | `opencode-go` | `minimax-m3` | `runs/conference/rux_approval_persistence_20260709/hermes_lead.md` |

## Main-Venue DeepSeek Pro Review

- Provider/model: DeepSeek supplier `deepseek-v4-pro`.
- Reasoning: maximum available effort. Verify logs/usage when possible.
- Forbidden: OpenCode Go `deepseek-v4-pro` for this main-venue high-risk review.
- Output: `runs/conference/rux_approval_persistence_20260709/main_deepseek_pro.md`

## Timeout And Retry Tracking

- Record each Hermes participant start/end time in `metrics/rux_approval_persistence_20260709_conference_metrics.md`.
- If a participant is slow, keep it `pending` while Codex continues local TDD.
- If a route fails, preserve stdout and use remaining participants/subagents.

## Codex Verification Checklist

- New tests watched fail before implementation.
- Focused tests pass after implementation.
- Full Python regression passes.
- Frontend build passes if frontend or public contract touched.
- Browser/API QC rerun if UI payloads or approval center behavior changed.
- No local path/hash/source field leakage in public payloads.
- Logs updated:
  - `logs/system_build_log.md`
  - `logs/subsystems/medical_monitoring_log.md`
  - `logs/subsystems/project_dashboard_log.md`
  - `logs/SOFT_PAUSE_*` if paused after this slice.
