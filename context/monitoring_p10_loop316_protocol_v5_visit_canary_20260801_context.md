# Task Context: monitoring_p10_loop316_protocol_v5_visit_canary_20260801

Created: 2026-08-01 01:30:29
Objective: Run exactly one new RUX protocol v5 visit_window_and_order canary against the frozen confirmed protocol; verify typed repair and all existing medical gates, perform read-only scientific contradiction review, make no candidate decision, retry no v4 job, and keep MY009 blocked.
Task type: `high_risk_contradiction_review`
Risk: `high`
Selected agent route: `codex` / `gpt-5.6-luna` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Current filesystem and runtime API/SQLite state are authoritative.
- Resume anchor:
  `context/monitoring_p10_loop316_protocol_typed_bundle_repair_pause_20260801.md`.
- Offline implementation review:
  `reviews/codex_monitoring_p10_loop316_protocol_typed_bundle_repair_20260801_review.md`.
- Prior v4 scientific audit:
  - `runs/execution/medical_monitoring_p10_20260730/loop_3_16_v16/rux_protocol_v4_candidate_audit.md`
  - `runs/execution/medical_monitoring_p10_20260730/loop_3_16_v16/rux_protocol_v4_candidate_audit.json`
  - `runs/codex-subagent_monitoring_p10_loop316_protocol_v4_audit_20260731.md`
- Current project/protocol:
  - project `proj_rux_03_002`
  - confirmed protocol version `protov_21c4b5a4a3883a8119d74e18`
  - canary topic `visit_window_and_order`
- Current implementation:
  - `services/api/app/monitoring_ai_source_packet.py`
  - `services/api/app/monitoring_ai_service.py`
  - `services/api/app/monitoring_protocol_preparation_service.py`
- Runtime authority is the 21 SQLite files directly under
  `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/runtime/`.

## Scope

- In scope:
  - create one fresh consistent pre-canary backup while services are stopped;
  - restore one and only one backend through `scripts/start_stable_backend.zsh`;
  - verify runtime readiness, independent product AI and current protocol prompt v5;
  - POST exactly one `visit_window_and_order` v5 job;
  - use one long hard wait, then GET terminal state;
  - inspect the immutable v5 attempt, candidate/evidence/repair lineage and source
    locators read-only;
  - run focused and adjacent regressions;
  - perform independent read-only contradiction review;
  - stop 8911 after the bounded slice and leave a durable checkpoint.
- Out of scope:
  - no v4 retry, batch start or salvage;
  - no candidate accept/reject/adopt/confirm/activate;
  - no mapping draft or activation;
  - no MY009;
  - no 5174/browser start;
  - no product-source edit unless the canary proves a narrowly reproducible defect and
    a separately tracked corrective slice is authorized;
  - no medical-writing business change.

## Success Criteria

- Pre-canary backup covers all 21 runtime SQLite files; every non-empty backup returns
  `PRAGMA integrity_check=ok`; empty files are byte-preserved.
- 8911 is the only backend listener and readiness is 200/ready with no missing
  capability.
- Independent AI remains configured and runnable without a Codex runtime dependency.
- Current protocol prompt identity is exactly
  `monitoring-protocol-clause-structuring-v5`.
- One and only one new v5 `visit_window_and_order` job is created; its job ID differs
  from the terminal v4 visit job `monai_e963986fbc88d53a1dd77f56c829`.
- No other topic gets a v5 job and no v4 job attempt count changes.
- Terminal outcome is observed after a single hard wait. A valid candidate, if any,
  must preserve provider-original claim anchors, carry typed server repair lineage,
  bind one exact table row plus available headers, remain within 50 IDs and pass all
  unchanged absence/eligibility/CM/IP/conflict gates.
- Scientific review must distinguish a valid structural candidate from a medically
  correct atomic visit rule; no candidate decision is made automatically.
- Focused monitoring and adjacent medical-writing regressions pass.
- 8911 is stopped at the end; MY009 remains blocked.

## Risk Boundaries

- The user-authorized real-project loop permits the one canary write and exact backup.
- Before the POST, freeze counts/job IDs/attempts for all eight protocol topics.
- The start endpoint may retry a terminal current-version job. Therefore call it only
  after confirming no current v5 visit job exists, and call it exactly once.
- Do not infer source support from repaired adjacency; repaired IDs are structural
  context only and must remain separated in lineage.
- The candidate decision boundary is user-owned.
- Do not run three real projects or start MY009.
- Preserve concurrent medical-writing files and databases; the backup is read-only
  against their source databases while services are stopped.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-01 01:30:29: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-01: Resume checkpoint re-read; all six implementation/test hashes match;
  no stale Kimi/Pi/Codex runner was present; 8911/5174 both had zero listeners.
- 2026-08-01: `visit_window_and_order` selected because the v4 failure was exact
  same-row condition/action binding, directly exercising the new typed table closure
  without expanding to another scientific topic.
- 2026-08-01: Pre-canary backup created at
  `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/runtime/backups/pre_loop316_protocol_v5_visit_canary_20260801_0135CST/`.
  It contains 21 main SQLite databases; 18 non-empty main databases returned
  integrity OK and 3 empty databases were byte-preserved. SQLite validation created
  auxiliary WAL/SHM files inside the backup directory; these are not additional main
  databases. Backup `medical_monitoring_ai.sqlite3` SHA-256 is
  `46d8f2411da6612860e36bd6f4e9d0e9c36aea357ac4e2a788bdfe608bb2e7aa`.
- 2026-08-01: First real startup exposed a cutover bug: global prompt retirement
  changed all eight v4 terminal jobs to stale and all eight proposed candidates to
  superseded. No canary POST occurred. Codex stopped 8911 and restored only
  `medical_monitoring_ai.sqlite3` from the pre-canary backup; integrity and the
  `2 completed / 6 failed / 8 proposed` baseline were restored.
- 2026-08-01: Separate finite-code correction
  `monitoring_p10_protocol_legacy_startup_recovery_fix_20260801` added explicit
  terminal-legacy preservation. Codex focused verification was 55 passed and Python
  compilation passed. A second real startup preserved the v4 baseline and restored the
  status projection to `2 candidate_review / 6 failed`.
- 2026-08-01: Readiness was 200/ready, runtime schema 16, missing capabilities empty.
  Independent AI was `alibaba_token_plan/qwen3.8-max-preview`,
  `semantic_ai_tasks_enabled=true`, `codex_runtime_dependency=false`.
- 2026-08-01: Exactly one POST with topic `visit_window_and_order` created new job
  `monai_5e1ed560631e7e0d6be5a948571a`, prompt v5, attempt 1. No other v5 job was
  created and no v4 attempt changed.
- 2026-08-01: After 10-minute and then 20-minute hard waits, the same job ended failed,
  not retryable, with no candidate:
  `provider output remained invalid after one controlled repair:
  MonitoringAiOutputValidationError: protocol structural repair cannot union list
  items across lists`.
- Immutable attempt:
  - attempt `monattempt_8f67d5f58b534b33b946fbb3699df33e`
  - provider model `qwen3.8-max-preview`
  - request 178,414 bytes; response 28,294 bytes
  - two provider outputs (initial + one controlled repair), each with five candidates
  - response SHA-256
    `8bd02c480ac4deec97e84bcef7110e42e1997741717081ded39e0f353c799e97`
- Parent observation: the first candidate remained a broad union of visit windows,
  rescheduling, lost follow-up, early withdrawal, safety follow-up, PK and drug
  dispensing/list evidence after repair. Other candidates were IP stop/restart,
  dispensing/adherence and withdrawal/safety mixtures. This suggests topical/atomic
  overaggregation, but independent review must determine whether exact
  `parent_match_source_ids` grouping also creates a false cross-list identity for
  items from one physical list.
- 8911 was stopped after terminal capture; 8911/5174 are both expected to have zero
  listeners during review.

## Independent Review Assignment

The native reviewer may read, but must not modify:

- this context;
- the exact runtime database
  `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/runtime/medical_monitoring_ai.sqlite3`
  in SQLite read-only mode, limited to job
  `monai_5e1ed560631e7e0d6be5a948571a`, its attempt/input packet, and the eight v4
  protocol jobs needed for comparison;
- `services/api/app/monitoring_ai_source_packet.py`;
- `services/api/app/monitoring_ai_service.py`;
- `services/api/app/monitoring_protocol_preparation_service.py`;
- prior v4 audit files already listed above.

Required questions:

1. For each of the five repaired provider candidates, identify the first deterministic
   validator failure and whether the candidate is atomic and in-topic.
2. Determine whether `parent_match_source_ids` exact-set grouping falsely separates
   items belonging to one physical list because the expander emits sliding context
   sets. Distinguish that from a genuinely cross-list candidate.
3. Decide whether the cross-list failure for this canary is correct fail-closed
   behavior, an identity-model defect, or both at different candidate/evidence levels.
4. Recommend the smallest next safe correction. If provider-visible selection or
   candidate atomicity changes, require a new prompt/job identity (v6); do not reuse or
   retry v5.
5. State whether any failed prose can be salvaged (expected default: no) and whether
   MY009/protocol gate remains blocked.
