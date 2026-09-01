# Task Context: monitoring_p10_loop316_protocol_v8_visit_canary_20260801

Created: 2026-08-01 08:59:24
Objective: Run exactly one new-ID RUX protocol v8 visit_window_and_order canary against the frozen confirmed protocol, preserve v4-v7 history, make no candidate decision, stop 8911 immediately after terminal evidence capture, and complete independent read-only scientific review before any expansion gate.
Task type: `high_risk_contradiction_review`
Risk: `high`
Selected agent route: `codex` / `gpt-5.6-luna` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Current filesystem and the 21 SQLite main databases directly under
  `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/runtime/`.
- Offline v8 resume anchor:
  `context/monitoring_p10_protocol_v8_reschedule_trigger_context_corrective_pause_20260801.md`.
- Offline v8 review:
  `reviews/codex_monitoring_p10_protocol_v8_reschedule_trigger_context_corrective_20260801_review.md`.
- Prior immutable v7 terminal evidence:
  `runs/monitoring_p10_loop316_protocol_v7_visit_canary_terminal_evidence_20260801.md`.
- Project `proj_rux_03_002`; confirmed protocol version
  `protov_21c4b5a4a3883a8119d74e18`; topic `visit_window_and_order`.
- Current implementation:
  - `services/api/app/monitoring_ai_service.py`
  - `services/api/app/monitoring_protocol_preparation_service.py`
  - `services/api/app/monitoring_ai_repository.py`

## Scope

- In scope:
  - create one fresh consistent backup of all 21 runtime SQLite main databases
    while 8911 and 5174 are stopped;
  - freeze v4-v7 RUX protocol job, attempt and candidate counts before startup and
    before the single POST;
  - start only the stable backend through `scripts/start_stable_backend.zsh`;
  - verify readiness, schema, capabilities, product-AI identity and history;
  - POST exactly once with only `visit_window_and_order`;
  - hard-wait once without repeat POST, retry, fixed controller polling or model
    status prompts;
  - capture terminal job/attempt, request/response hashes, repair count,
    candidates/failure, diagnostics, source locators and persistence;
  - stop 8911 immediately after terminal capture;
  - reuse the existing Luna reviewer session for read-only scientific,
    structural and contradiction review;
  - run focused monitoring, full monitoring and adjacent medical-writing
    regression gates after terminal capture.
- Out of scope:
  - retry, reuse or salvage of v4-v7 jobs or responses;
  - candidate accept/reject/adopt/confirm/activate;
  - mapping draft/activation;
  - MY009, another topic, another real project, 5174 or browser;
  - product or medical-writing source edits.

## Success Criteria

- Backup contains exactly 21 DB copies; all 18 non-empty copies return
  `PRAGMA integrity_check=ok` under read-only immutable access and the three empty
  DBs remain zero bytes.
- Startup is ready at schema 16 with no missing capability; only 8911 listens and
  product AI is independently configured.
- Product protocol prompt is exactly
  `monitoring-protocol-clause-structuring-v8`.
- Startup preserves v4-v7 jobs, attempts and candidates and creates no v8 state.
- Exactly one new v8 visit job is created with one attempt and no other v8 topic.
- Terminal behavior is observed without repeat POST or retry. Success requires
  only allowed visit fact types, exactly one operative visit family, no
  IP/CM/PK/withdrawal/safety/collection content, exact source evidence and valid
  packet/repair lineage. Failure must persist zero candidates with complete
  indexed diagnostics and no partial salvage.
- At most one controlled repair occurs and the response is immutable.
- 8911 is stopped after terminal capture; 5174 and MY009 remain blocked.
- Independent review plus Codex verification determines the gate. No candidate
  decision is made.

## Risk Boundaries

- Runtime writes are limited to the backup, backend startup recovery and exactly
  one authorized new v8 visit start/attempt.
- The start API can retry a same-identity terminal job; it may be called exactly
  once only after proving v8 count is zero.
- Candidate decisions remain user-owned.
- Do not run another topic/project, start 5174, or modify product/medical-writing
  sources.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- One canary POST followed by one uninterrupted hard-wait observer with a
  30-minute ceiling. The observer may query read-only status internally but the
  parent must not issue fixed-interval controller calls.
- No repeat POST, retry or re-dispatch. Terminal success, terminal failure or the
  hard-wait ceiling ends observation; 8911 is then stopped before analysis.
- Independent review reuses the existing native Luna session. Do not re-dispatch
  because of latency.

## Loop Log

- 2026-08-01 08:59:24: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-01: Latest global/project AGENTS and the verification-loop skill were
  reread. The five governed v8 hashes match the offline pause anchor. 8911/5174
  have no listeners; v4/v5/v6/v7 remain `8/1/1/1` jobs,
  `8/1/1/1` attempts and `8/0/0/0` candidates; v8 is empty.
- 2026-08-01: Fresh pre-canary backup created at
  `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/runtime/backups/pre_loop316_protocol_v8_visit_canary_20260801_0859CST/`.
  Exactly 21 main DB copies exist; 18 non-empty copies returned immutable
  `PRAGMA integrity_check=ok` and three empty DBs were byte-preserved. Backup
  `medical_monitoring_ai.sqlite3` SHA-256:
  `db8d057d054b972b227c2fe281e31388effed2cbf6cacbe85d1a8bcbb5a0d350`.
- 2026-08-01: Unique 8911 startup through
  `scripts/start_stable_backend.zsh` passed the pre-POST gate:
  readiness 200/ready, schema 16, no missing capabilities, independent product
  AI `alibaba_token_plan/qwen3.8-max-preview`, no Codex runtime dependency,
  v4-v7 history unchanged and v8 empty. Only 8911 listened; 5174 stayed
  stopped.
- 2026-08-01: Exactly one POST with only `visit_window_and_order` returned 202
  and created v8 job `monai_06e9dd4e1b18677ff748ed792445`, source revision
  `mpr_40b82826a43e46342344841242e6`. No other topic or project was started.
- 2026-08-01: The single hard-wait observer returned terminal failed /
  `invalid_ai_output` at `2026-08-01T01:10:55.753384+00:00`. Attempt
  `monattempt_e635a4f195ae4784b825a9be12399e8b` contains initial plus one
  controlled repair and zero persisted candidates. Request SHA-256 is
  `87bfc229bf678d11dfd8fc330f2609c9998be7c6dae596228a4c92ab6f3a9488`;
  response SHA-256 is
  `aba303673d7585e9aa620b44cb70b8129e080f94bc50fd9f6f8eeed01a40e234`.
- 8911 was gracefully stopped immediately after terminal capture; 8911/5174
  now have zero listeners. v4-v7 counts stayed frozen and v8 is one job / one
  attempt / zero candidates. Detailed extract:
  `runs/monitoring_p10_loop316_protocol_v8_visit_canary_terminal_evidence_20260801.md`.
- Post-canary focused monitoring passed 376 and adjacent medical-writing passed
  200. The normal full-monitoring selector was blocked at collection by a
  concurrent medical-writing edit: the source no longer exports
  `_REQUIRED_CORE_BODY_SEMANTIC_IDS` while a pre-existing writing test imports
  it. This task did not modify or restore either file; a monitoring rerun
  excludes only that unrelated collection blocker.
- The bounded full-monitoring rerun excluding only
  `tests/test_medical_writing_dynamic_section_matrix.py` passed
  `1371 passed, 4283 deselected, 27 warnings in 731.00s`. This proves the
  monitoring selection remains green, but it does not turn the standard
  repository selector green while the concurrent writing import drift remains.
- The existing Luna reviewer `/root/rux_protocol_v4_audit` was reused after
  guard preflight and returned **FAIL CLOSED**. It confirmed safe runtime
  fail-closed behavior, scientifically coherent single-topic cores for
  candidates 1-4, executable-contract noncompliance in user-visible scope
  disclaimers/guidance, and a bounded postpositive reschedule-trigger false
  positive. It rejected weakening full-boundary checks, broad negation
  exceptions or global reschedule precedence.
- Final gate: v8 is immutable terminal evidence and must not be retried, reused
  or salvaged. MY009/other topics remain blocked. The next safe slice is an
  offline fresh-prompt corrective limited to provider-visible exclusion wording
  across all user-visible fields plus the postpositive reschedule-trigger role,
  with the existing strict gates preserved.
