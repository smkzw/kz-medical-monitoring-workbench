# Conference Context: rux_monitoring_inbox_detail_20260708

Created: 2026-07-08 14:24:59
Objective: Migrate 医学监查 RUX risk list/detail from demo rows to real workbench inbox items with action/audit browser QC
Task type: `complex_delivery_conference`
Risk: `high`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Hermes Sub-Venue

- Lead/chair: OpenCode Go `minimax-m3`.
- Participant models: OpenCode Go `qwen3.7-plus`, OpenCode Go `mimo-v2.5`, and DeepSeek supplier `deepseek-v4-flash`, all default reasoning effort unless Codex overrides.
- All `deepseek-v4-flash` routes must use the DeepSeek supplier. OpenCode Go `deepseek-v4-flash` is not allowed for this workflow.
- `qwen3.7-plus` must be smoke-tested in this route because it recently had intermittent run errors.
- Main-venue high-risk reviewer: DeepSeek supplier `deepseek-v4-pro` only. OpenCode Go `deepseek-v4-pro` is not allowed for this role.

## Source Of Truth

- User requirements in current active goal and prior corrections:
  - full medical-manager workbench must become commercial-deliverable, tested on real project data/files, not demo-only.
  - RUX medical monitoring must start from real project-level data listing and protocol-derived rules, not pre-baked skill outputs.
  - `CM` is non-investigational concomitant medication/treatment only; trial-drug dose adjustment/pause/restart must remain separate.
  - Chinese clinical wording must fit clinical-trial medical-manager context.
- Current local workbench files:
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
- Runtime/browser evidence from previous pass:
  - `records/visual_qc_20260708/rux_three_subject_category_colors/rux_three_subject_drilldown_metrics.json`
  - `records/visual_qc_20260708/rux_subject_timeline_category_colors/subject_timeline_ip_lane_metrics.json`
- Real project payload evidence should be inspected via local API when needed:
  - `GET /api/projects/proj_rux_03_002/workbench-inbox`
  - `GET /api/projects/proj_rux_03_002/subjects/{subject_id}/monitoring`

## Scope

- In scope:
  - make 医学监查 risk list and risk detail use real `workbench-inbox` items for RUX project mode;
  - preserve demo fallback only when no real project inbox items are available;
  - selecting a RUX risk must select the correct real subject and support drilldown to Subject Timeline and Patient Profile;
  - action buttons must call backend workbench inbox action/audit route where feasible and must not silently mutate/delete unread items;
  - browser QC must verify real RUX item titles/subjects, no demo subject/risk leakage, action/audit persistence, and no desktop/mobile overflow.
- Out of scope for this slice:
  - broad redesign of all medical monitoring UI;
  - automatic EDC integration;
  - formal medical conclusion generation beyond existing backend risk item payload;
  - modifying original project source files under `/Users/smkzw/Documents/康哲项目资料` or `/Users/smkzw/Documents/朗来项目资料`.

## Success Criteria

- Static/TDD:
  - a frontend contract test proves `MonitoringPage` receives and maps `workbenchInbox` risk items and does not rely on legacy `riskRows` when inbox risk items exist.
  - tests prove RUX risk text uses real subject ids/titles such as S01003/S01017/S03040 and rejects demo risk subjects/titles in RUX mode.
- Runtime/browser:
  - desktop and mobile browser QC on `proj_rux_03_002` show real RUX risk items in 医学监查;
  - clicking a risk item updates detail panel and selected subject;
  - detail panel exposes evidence/source metadata and action controls without local path leakage;
  - Subject Timeline and Patient Profile entry buttons open the selected real subject;
  - a safe action such as `mark_read` persists through backend action/audit endpoint or the QC records why the current route blocks it;
  - no horizontal overflow.
- Regression:
  - `npm run build` succeeds;
  - relevant focused backend/frontend tests pass;
  - full `python3 -m unittest discover -s tests -v` passes before claiming completion.
- Records:
  - update medical monitoring and system logs with decisions, pitfalls, commands, browser QC artifacts, remaining gaps.

## Parallel Work Rule

For logic-heavy, rigor-sensitive, or artifact-heavy tasks, each participant independently runs the whole bounded workflow and writes a separate output. Leads compare after all available participant outputs are in or explicitly marked pending.

## Timeout Policy

- Participant soft wait: 20 minutes.
- Large-task participant wait: 45 minutes.
- Lead/main hard wait: 90 minutes.
- Failure rule: Do not fail a model for slow response alone; fail only on terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Risk Boundaries

- Hermes is advisory; Codex remains final authority.
- Codex owns visual/browser/PPT/PDF/rendered checks, live authority checks, final clinical/regulatory conclusions, and production writes.
- Do not mark a slow model failed solely due to latency.

## Loop Log

- 2026-07-08 14:24:59: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-07-08 14:29-14:34: Participant outputs completed for `qwen3.7-plus`, `mimo-v2.5`, and DeepSeek supplier `deepseek-v4-flash`.
- 2026-07-08 14:45: Hermes sub-venue chair `minimax-m3` wrote `runs/conference/rux_monitoring_inbox_detail_20260708/hermes_lead.md`.
- 2026-07-08 14:41-14:57 Codex implementation/verification evidence available before main-venue review:
  - `frontend/src/App.jsx` contains `monitoringRiskRowsFromInbox(workbenchInbox)`, `MonitoringPage(... workbenchInbox, refreshWorkbenchInbox)`, real inbox row mapping, source ref labels, and `mark_read` action route with `comment="opened_from_monitoring_detail"`.
  - `tests/test_frontend_monitoring_contract.py` defines the static contract for real inbox preference, source refs/unread state mapping, prop wiring, and unsupported disposition removal.
  - `frontend/tests/rux_monitoring_inbox_qc.mjs` exercises the live RUX project in desktop and mobile browser states, backs up/restores the action store, opens a real S01017 risk, performs `mark_read`, then drills into Subject Timeline and Patient Profile.
  - Focused static regression: `python3 -m unittest tests.test_frontend_monitoring_contract -v` passed 4 OK.
  - Production frontend build: `npm run build` passed with known Vite chunk-size warning only.
  - Browser QC refreshed `records/visual_qc_20260708/rux_monitoring_inbox/rux_monitoring_inbox_metrics.json`; desktop/mobile both showed 4 real RUX risks, S01003/S01017/S03040 real subjects, no demo/internal leakage, no horizontal overflow, unread count 4 -> 3 after mark_read, total open count stayed 4, selected item remained in inbox with `unread=false`, and Subject Timeline/Patient Profile handoff for S01017 passed.
  - Full regression from the same continuation: `python3 -m unittest discover -s tests -v` passed 141 OK.
