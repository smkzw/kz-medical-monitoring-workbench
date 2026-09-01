# Task Context: monitoring_p10_loop316_protocol_v7_visit_canary_20260801

Created: 2026-08-01 06:37:47
Objective: Run exactly one new-ID RUX protocol v7 visit_window_and_order canary against the frozen confirmed protocol, preserve v4-v6 history, make no candidate decision, stop 8911 after terminal evidence capture, and perform independent read-only scientific review before any expansion gate.
Task type: `high_risk_contradiction_review`
Risk: `high`
Selected agent route: `codex` / `gpt-5.6-luna` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Current filesystem, runtime APIs, and the 21 SQLite main databases directly under
  `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/runtime/`.
- Resume anchor:
  `context/monitoring_p10_loop316_protocol_v7_visit_scope_atomicity_corrective_pause_20260801.md`.
- Offline v7 acceptance:
  `reviews/codex_monitoring_p10_protocol_v7_visit_scope_atomicity_corrective_20260801_review.md`.
- Independent offline final recheck:
  `runs/codex-subagent_monitoring_p10_protocol_v7_visit_scope_atomicity_corrective_20260801_final_recheck.md`.
- Project `proj_rux_03_002`; confirmed protocol version
  `protov_21c4b5a4a3883a8119d74e18`; topic `visit_window_and_order`.
- Current implementation:
  - `services/api/app/monitoring_ai_service.py`
  - `services/api/app/monitoring_protocol_preparation_service.py`
  - `services/api/app/monitoring_ai_repository.py`
- Current five governed hashes are recorded in the resume anchor and were
  reverified before task initialization.

## Scope

- In scope:
  - while services are stopped, create one fresh consistent backup of all 21 runtime
    SQLite main databases and verify all non-empty copies;
  - freeze v4-v6 RUX protocol job IDs, status, attempt and candidate counts before
    startup and before POST;
  - start the unique backend only through `scripts/start_stable_backend.zsh`;
  - verify readiness/schema/capabilities and independent product AI identity;
  - prove startup preserves v4-v6 history and all eight proposed v4 candidates;
  - prove no v7 protocol job exists before POST;
  - POST exactly once with only `visit_window_and_order`;
  - hard-wait without repeat POST, retry, fixed controller polling or model status
    prompts;
  - capture terminal job/attempt, immutable request/response, controlled repair
    count, candidates or failure, diagnostics, source locators and persistence;
  - stop 8911 immediately after terminal evidence capture;
  - reuse the existing native Luna reviewer session for one read-only scientific,
    structural and contradiction review;
  - run only the post-canary focused monitoring and adjacent medical-writing
    regression required by the outcome.
- Out of scope:
  - v4/v5/v6 claim, retry, reuse, or prose salvage;
  - candidate accept/reject/adopt/confirm/activate;
  - mapping draft/activation;
  - MY009, other real projects, 5174 or browser;
  - product source edits; any isolated defect requires a separately tracked offline
    corrective slice;
  - medical-writing business changes.

## Success Criteria

- The pre-canary backup contains exactly 21 main DB copies; all 18 non-empty copies
  return `PRAGMA integrity_check=ok` and the three empty DBs remain zero bytes.
- Startup readiness is ready with schema 16 and no missing capability; only 8911
  listens.
- Product protocol prompt is exactly
  `monitoring-protocol-clause-structuring-v7`.
- Startup preserves the complete v4-v6 baseline and eight v4 proposed candidates;
  startup creates no v7 job or candidate.
- Exactly one new v7 visit job is created with a distinct ID and one attempt. No
  other v7 topic is created and all v4-v6 attempt counts remain frozen.
- Terminal behavior is observed without repeat POST or retry:
  - success requires only allowed visit fact types, exactly one operative family,
    no IP/CM/PK/withdrawal/safety/collection content, exact source evidence and
    valid packet-v3/repair-v2 lineage;
  - failure must persist zero candidates with complete candidate-indexed ordered
    diagnostics and no partial salvage.
- The attempt contains at most one controlled repair and the response is immutable.
- 8911 is stopped after terminal capture; 5174 and MY009 remain blocked.
- Independent review plus Codex verification determines the next gate. No candidate
  decision is made.

## Risk Boundaries

- Runtime writes are limited to the consistent backup, backend startup recovery and
  exactly one authorized new v7 visit start/attempt.
- Before POST, verify v7 count is zero and persist the v4-v6 baseline.
- The `start` API can retry a same-identity terminal job. Call it exactly once only
  after the zero-v7 proof.
- Candidate decisions are user-owned.
- Do not run other real projects, start 5174, or modify product/medical-writing
  sources during this task.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- One canary POST and one uninterrupted 10-minute hard wait; if still non-terminal,
  one additional uninterrupted 20-minute hard wait. No repeat POST, retry, fixed
  status loop or controller model prompt.
- Terminal failure, terminal success, or the end of the second hard wait ends the
  runtime observation. Stop 8911 before analysis.
- Independent review reuses the existing native Luna session. Do not re-dispatch
  because of latency; use the runtime hard wait and the same handle.

## Loop Log

- 2026-08-01 06:37:47: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-01: Latest global/project AGENTS were read in full. Their SHA-256 values
  remain `28029e...cd79` and `31d8b1...b001`. Five governed v7 hashes match the
  pause anchor; offline review gate remains PASS; 8911/5174 and monitoring workers
  have zero active process/listener state.
- 2026-08-01: Read-only pre-start baseline:
  - v4: 8 jobs / 8 attempts / 8 proposed candidates
    (`2 completed / 5 failed / 1 stale_input`);
  - v5 visit: `monai_5e1ed560631e7e0d6be5a948571a`, failed, attempt 1,
    zero candidates;
  - v6 visit: `monai_93160e1e698569730d331fa50f6e`, failed, attempt 1,
    zero candidates;
  - v7: zero jobs / attempts / candidates.
- 2026-08-01: Fresh pre-canary backup created at
  `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/runtime/backups/pre_loop316_protocol_v7_visit_canary_20260801_0638CST/`.
  Exactly 21 main SQLite files exist; 18 non-empty copies returned
  `PRAGMA integrity_check=ok` under `mode=ro&immutable=1`, and three empty copies
  were byte-preserved. Backup `medical_monitoring_ai.sqlite3` SHA-256:
  `36793874f0c0597427cac07403f1b19bb17f13acc8a81d9569b33395e3cc4367`.
  The first `-readonly` validation form emitted SQLite open warnings for some
  WAL-derived copies and was not accepted; the strict immutable recheck is the
  retained evidence.
- 2026-08-01: Unique 8911 startup through `scripts/start_stable_backend.zsh`
  passed its pre-POST gate:
  - `/api/runtime-readiness` returned 200/ready, schema 16, and no missing
    capabilities;
  - independent product AI is
    `alibaba_token_plan/qwen3.8-max-preview`, OpenAI-compatible transport,
    `codex_runtime_dependency=false`, with no route validation errors;
  - API status remained `2 candidate_review / 6 failed`; all v4-v6 job IDs,
    attempts and candidate counts were unchanged;
  - source declares active prompt
    `monitoring-protocol-clause-structuring-v7`, while runtime DB still contains
    zero v7 jobs;
  - only 8911 listens; 5174 remains stopped.
  One read-only probe to obsolete `/api/runtime/ai-settings` returned 404; it made
  no state change and was replaced by the current `/api/ai-gateway/status` route.
- 2026-08-01: Exactly one POST with only `visit_window_and_order` returned 202 and
  created new v7 job `monai_d3c770a87e60007b47ad9a105091`, source revision
  `mpr_40b82826a43e46342344841242e6`. The worker claimed only this job as attempt 1;
  all v4-v6 job/attempt/candidate counts remained frozen and v7 candidate count was
  zero at hard-wait entry. No other v7 topic exists.
- 2026-08-01: After one uninterrupted 10-minute hard wait, the same v7 job was
  terminal `failed / invalid_ai_output`, attempt 1, zero candidates. Request
  SHA-256 is `ff942e...4d05` (162,194 bytes); response SHA-256 is
  `2c5cd6...7522` (14,037 bytes). The attempt contains exactly two provider
  outputs: initial plus one controlled repair.
- The initial repair diagnostics contained the complete indexed errors for
  candidates 1, 2, 3 and 5. The repaired response closed every listed topic-boundary
  error and left only candidate 2 `计划访视改期原则` failing exactly-one-family.
  Static replay shows schedule hits (`计划访视`, `访视窗`) and reschedule hits
  (`改期`, `重新安排`) in this otherwise rescheduling-only clause.
- 8911 was gracefully stopped immediately after terminal capture; 8911/5174 have
  zero listeners. v4-v6 counts remained frozen; v7 is one job / one attempt /
  zero candidates. Detailed extract:
  `runs/monitoring_p10_loop316_protocol_v7_visit_canary_terminal_evidence_20260801.md`.
- 2026-08-01: Post-canary focused monitoring passed `336` and adjacent
  medical-writing passed `200`; no product source changed.
- 2026-08-01: Prompt preflight passed after converting the runner output declaration
  to the guard's required inline syntax. The existing Luna review session was reused
  once; no new reviewer or fallback route was created.
- Independent verdict: FAIL CLOSED. Candidate 2 is scientifically a single
  reschedule condition-action rule; the deterministic classifier falsely counts
  `计划访视/访视窗` in title/trigger condition as an independent schedule family.
  Runtime safety mechanisms passed, but the functional canary did not.
- Final gate: v7 terminal output remains immutable and unsalvaged. The next safe
  action is a separately tracked offline v8 prompt/classifier corrective limited to
  reschedule-trigger context, exact positive/negative tests and full regressions.
  MY009 and all expansion remain blocked.
