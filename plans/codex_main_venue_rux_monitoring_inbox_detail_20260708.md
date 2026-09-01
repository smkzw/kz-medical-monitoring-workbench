# Codex Main-Venue Plan: rux_monitoring_inbox_detail_20260708

Date: 2026-07-08
Objective: Migrate 医学监查 RUX risk list/detail from demo rows to real workbench inbox items with action/audit browser QC

## Task Decomposition

1. Inspect the current `MonitoringPage` data flow and backend workbench inbox action route.
2. Add a failing frontend contract test that defines the desired real-inbox behavior.
3. Implement minimal frontend mapping:
   - use real inbox items when present;
   - preserve legacy demo fallback only when inbox items are absent;
   - expose reader-facing risk detail fields and evidence/source refs;
   - set selected subject from the clicked risk item.
4. Wire at least one safe action to backend audit, preferably `mark_read`, and preserve action feedback in the UI.
5. Add/extend browser QC to verify real RUX risk list/detail and drilldown handoff.
6. Run focused tests, build, browser QC, then full regression.
7. Log decisions, failures, evidence, and remaining gaps.

## Source Packet

- `frontend/src/App.jsx`
- `frontend/src/styles.css`
- `frontend/tests/subject_timeline_ip_lane_qc.mjs`
- `frontend/tests/rux_three_subject_drilldown_qc.mjs`
- `tests/test_frontend_timeline_contract.py`
- `tests/test_workbench_inbox.py`
- `tests/test_rux_monitoring_service.py`
- `services/api/app/workbench_inbox.py`
- `services/api/app/main.py`
- `services/api/app/rux_monitoring_service.py`
- `packages/contracts/workbench_contracts/models.py`
- `logs/subsystems/medical_monitoring_log.md`
- `logs/system_build_log.md`
- local API: `GET /api/projects/proj_rux_03_002/workbench-inbox`
- local API: `GET /api/projects/proj_rux_03_002/subjects/{subject_id}/monitoring`

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `participant_qwen_plus` | `opencode-go` | `qwen3.7-plus` | `runs/conference/rux_monitoring_inbox_detail_20260708/participant_qwen_plus.md` |
| `participant_mimo` | `opencode-go` | `mimo-v2.5` | `runs/conference/rux_monitoring_inbox_detail_20260708/participant_mimo.md` |
| `participant_ds_flash` | `deepseek` | `deepseek-v4-flash` | `runs/conference/rux_monitoring_inbox_detail_20260708/participant_ds_flash.md` |

## Hermes Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `hermes_lead` | `opencode-go` | `minimax-m3` | `runs/conference/rux_monitoring_inbox_detail_20260708/hermes_lead.md` |

## Main-Venue DeepSeek Pro Review

- Provider/model: DeepSeek supplier `deepseek-v4-pro`.
- Reasoning: maximum available effort. Verify logs/usage when possible.
- Forbidden: OpenCode Go `deepseek-v4-pro` for this main-venue high-risk review.
- Output: `runs/conference/rux_monitoring_inbox_detail_20260708/main_deepseek_pro.md`

## Timeout And Retry Tracking

- Record start/end time, pending/failed/incorporated status, retry reason, and whether late outputs were used.
- Slow participant output remains `pending` until hard timeout/retry rules are met.

## Codex Verification Checklist

- Static contract test proves `MonitoringPage` accepts and prefers real `workbenchInbox` risk items.
- Browser QC proves RUX risk list/detail show real items and no legacy demo risks.
- Clicking a real risk updates selected subject and Subject Timeline/Patient Profile drilldown.
- Safe action/audit route is exercised or explicitly recorded as blocked by current backend contract.
- No local absolute paths in frontend source.
- `npm run build` succeeds.
- Full `python3 -m unittest discover -s tests -v` succeeds before completion claim.

## Decisions Pending

- Safest repeatable QC action: default candidate `mark_read`.
- Evidence display boundary: show source domain/row locator/summary, not local file paths.
- Additional disposition actions beyond read/audit are deferred unless current backend already supports them safely.
