# Task Context: monitoring_p10_loop316_protocol_v6_visit_canary_20260801

Created: 2026-08-01 03:34:07
Objective: Run exactly one new RUX protocol v6 visit_window_and_order canary against the frozen confirmed protocol, preserve all v4/v5 history, make no candidate decision, stop 8911 after terminal evidence capture, and perform independent read-only scientific review before any gate decision.
Task type: `high_risk_contradiction_review`
Risk: `high`
Selected agent route: `codex` / `gpt-5.6-luna` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Current filesystem, runtime APIs, and the 21 SQLite databases directly under
  `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/runtime/`.
- Resume anchor:
  `context/monitoring_p10_loop316_protocol_v6_identity_atomicity_corrective_pause_20260801.md`.
- v6 offline acceptance:
  `reviews/codex_monitoring_p10_protocol_v6_identity_atomicity_corrective_20260801_review.md`.
- v5 immutable review:
  `runs/codex-subagent_monitoring_p10_loop316_protocol_v5_visit_canary_20260801.md`.
- Project `proj_rux_03_002`; confirmed protocol version
  `protov_21c4b5a4a3883a8119d74e18`; topic `visit_window_and_order`.
- Current implementation:
  - `services/api/app/monitoring_ai_source_packet.py`
  - `services/api/app/monitoring_ai_service.py`
  - `services/api/app/monitoring_protocol_preparation_service.py`
- Current seven-file SHA-256 baseline is recorded in the resume anchor and was
  independently reverified before this task.

## Scope

- In scope:
  - while services are stopped, create one fresh consistent backup of all 21 runtime
    SQLite main databases and verify every non-empty backup with
    `PRAGMA integrity_check=ok`;
  - freeze all RUX protocol job IDs, prompt versions, statuses, attempts and candidate
    counts before startup and before POST;
  - start the unique backend only through `scripts/start_stable_backend.zsh`;
  - verify startup preserves v4/v5 terminal history and all eight proposed v4
    candidates;
  - verify ready/schema/capabilities and independent product AI identity;
  - confirm there is no existing v6 visit job;
  - POST exactly once for only `visit_window_and_order`;
  - use the same runner/job hard-wait discipline: no repeat POST, no retry, no
    controller status prompts during the wait;
  - capture one terminal v6 attempt, immutable response, candidates or failure, exact
    structural repair lineage and source locators read-only;
  - stop 8911 after terminal capture;
  - reuse the existing native Luna reviewer session for one independent read-only
    scientific/structural review;
  - run focused monitoring and adjacent medical-writing regressions.
- Out of scope:
  - v4/v5 retry or reuse; batch start for other protocol topics;
  - candidate accept/reject/adopt/confirm/activate;
  - mapping draft/activation;
  - MY009, the three-real-project sequence, 5174/browser;
  - product source edits unless a new defect is isolated into a separately tracked
    offline corrective slice;
  - medical-writing business changes.

## Success Criteria

- Pre-canary backup contains exactly 21 main DB copies; all 18 non-empty databases
  are integrity OK and the 3 empty databases are byte-preserved.
- Startup readiness is ready with schema 16 and no missing capability; only 8911
  listens.
- Current protocol prompt is exactly
  `monitoring-protocol-clause-structuring-v6`.
- v4 history remains 2 completed / 5 failed / 1 stale visit, v5 visit remains one
  failed terminal job, and all 8 v4 candidates remain proposed; startup creates no
  job or candidate.
- Exactly one new v6 visit job is created, with a new job ID and one attempt. No other
  v6 topic exists and no v4/v5 attempt count changes.
- Terminal result is observed without repeat POST/retry. A successful candidate must
  have an allowed visit fact type, exactly one visit action family, no IP/CM/PK/
  withdrawal/safety/collection content, exact source evidence, and valid packet-v3 /
  repair-v2 lineage. A failure must remain zero-candidate and be independently
  diagnosed; failed prose is not salvaged.
- 8911 is stopped after evidence capture; MY009 remains blocked.
- Independent review and Codex regressions determine the next gate; no candidate
  decision is made.

## Risk Boundaries

- Runtime writes are limited to the one consistent backup, backend startup recovery,
  and exactly one authorized v6 visit start/attempt.
- Before POST, verify v6 visit count is zero and persist the complete eight-topic
  baseline.
- `start` may reuse/retry an existing current-version terminal job; therefore it must
  be called once only after the zero-v6 check.
- Candidate decisions are user-owned.
- Do not run other real projects, start 5174, or modify product/medical-writing
  sources during this canary task.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- One canary POST and one uninterrupted hard-wait window, up to 120 minutes.
- Do not use fixed-interval model/controller polling or re-dispatch for latency.
- Terminal failure, runner hard-wait return, or a persisted terminal job ends the wait.
- Independent review reuses the existing native Luna session; no new reviewer unless
  that handle is unavailable or terminally failed.

## Loop Log

- 2026-08-01 03:34:07: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-01: Resume anchor reread. Global AGENTS hash unchanged; seven v6 file
  hashes match; 8911/5174 have zero listeners; no medical-monitoring runner is
  active. An unrelated MeetingMinutesMac manager remains isolated and untouched.
- 2026-08-01: Read-only runtime baseline integrity is OK. Protocol history currently
  has v4 `2 completed / 5 failed / 1 stale_input`, one failed v5 visit job, eight
  proposed v4 candidates, zero v6 jobs, and no queued/running protocol job.
- 2026-08-01: Consistent pre-canary backup completed at
  `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/runtime/backups/pre_loop316_protocol_v6_visit_canary_20260801_0340CST/`.
  It contains 21 main SQLite databases; 18 non-empty copies returned integrity OK and
  3 empty databases were byte-preserved. Integrity checks created 30 WAL/SHM auxiliary
  files in the backup directory, for 51 files total. Backup
  `medical_monitoring_ai.sqlite3` SHA-256 is
  `1756df1034bcf68a7d7f7e7018fce9ae869395b43635b730f262168de7ebf9b4`.
  Two incomplete task-created attempts were moved to macOS Trash as recoverable
  directories after diagnosing WAL-mode read-only validation behavior; no source DB
  was removed or overwritten.
- 2026-08-01: Unique 8911 startup passed: runtime ready, schema 16, no missing
  capabilities, independent AI `alibaba_token_plan/qwen3.8-max-preview`, no Codex
  dependency. Startup preserved v4 `2 completed / 5 failed / 1 stale_input`, the
  failed v5 visit job, and all 8 proposed v4 candidates; v6 job count remained zero.
- 2026-08-01: Exactly one POST for only `visit_window_and_order` created v6 job
  `monai_93160e1e698569730d331fa50f6e`, source revision
  `mpr_40b82826a43e46342344841242e6`, attempt 1. No other v6 job was created and
  v4/v5 attempt counts did not change.
- 2026-08-01: After one 10-minute and one additional 20-minute hard wait, the same
  job was terminal failed / `invalid_ai_output` / zero candidates:
  `provider output remained invalid after one controlled repair:
  MonitoringAiOutputValidationError: visit protocol candidate must contain exactly
  one visit action family`.
- Immutable attempt:
  - `monattempt_a4d6ee94c29040fc97fb740963f2fce6`
  - request 166,992 bytes; response 23,666 bytes
  - response SHA-256
    `b6939be6675b5cdb1686e12332a1bd540fbd9d142e0254808b0262901b1b22ac`
  - two provider outputs, initial + one controlled repair, each with five candidate
    objects; no candidate persisted.
- Parent pre-review observation: the repair removed dispensing/adherence/PK details
  from some candidates but candidate 1 still combined a schedule/window family with
  rescheduling and retained “访视当天首次用药” IP-administration content. Other repaired
  candidates still include safety follow-up/AE-CM collection, early withdrawal/
  consent withdrawal/lost follow-up, unscheduled visit, or first-dose IP content.
  Independent review must determine the exact validator order, whether the visit
  medication gate incompletely covers administration, and whether any otherwise
  valid atomic visit candidate exists. No prose may be salvaged by default.
- 8911 was gracefully stopped immediately after terminal capture; 8911/5174 both
  have zero listeners during review.
- 2026-08-01: Prompt preflight passed with no warnings. The existing native Luna
  reviewer session `/root/rux_protocol_v4_audit` was resumed once and completed a
  read-only contradiction review; no new reviewer or fallback was dispatched.
- Independent review found all five repaired candidates structurally closed but
  unsafe. C1/C2 retained first-dose IP administration and mixed schedule with
  rescheduling; C3/C4 retained withdrawal/safety/collection or mixed visit families;
  C5 remained an IP-administration clause.
- The review confirmed `_VISIT_TOPIC_MEDICATION_ACTION_RE` does not cover
  first-dose/administration wording, current family detection is noisy across
  review-only fields, and one-repair diagnostics expose only the first
  response-level failure.
- Codex verification after terminal capture: focused monitoring four-file suite
  `254 passed`; adjacent medical-writing five-file suite `200 passed`; no failures.
- Final gate: v6 failed closed and must not be retried or reused. RUX protocol is
  NO-GO; MY009 and all three real projects remain blocked. Next safe action is a
  separately tracked offline v7 scope/atomicity corrective; 8911/5174 must remain
  stopped until that slice passes its complete negative-test matrix.
