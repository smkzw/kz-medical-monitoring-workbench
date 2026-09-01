# Task Context: monitoring_p10_protocol_v7_visit_scope_atomicity_corrective_20260801

Created: 2026-08-01 04:29:19
Objective: Implement an offline v7 visit-topic scope and atomicity corrective: field-aware IP/CM administration, withdrawal and AE/CM collection gates; operative-only visit-family classification; complete candidate-indexed repair diagnostics; prompt v7; full negative tests, without starting services or real projects
Task type: `finite_code_task`
Risk: `high`
Selected agent route: `deepseek` / `deepseek-v4-flash` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Current filesystem under this workbench.
- v6 terminal review:
  `runs/codex-subagent_monitoring_p10_loop316_protocol_v6_visit_canary_20260801.md`.
- v6 pause:
  `context/monitoring_p10_loop316_protocol_v6_visit_canary_pause_20260801.md`.
- Implementation:
  - `services/api/app/monitoring_ai_service.py`
  - `services/api/app/monitoring_protocol_preparation_service.py`
- Direct tests:
  - `tests/test_monitoring_ai_service.py`
  - `tests/test_monitoring_protocol_preparation.py`
  - `tests/test_monitoring_ai_api.py`
- Current protocol evidence/repair contracts remain packet v3 / structural repair
  v2. This slice must not change them.
- Baseline SHA-256:
  - `monitoring_ai_service.py`:
    `6ae0e01037880bc881cf03017ae10ebf5e62660c5eafcad5c4d671cfec48bb3f`
  - `monitoring_protocol_preparation_service.py`:
    `d8492de18b734fdc3cf9caeffc2a0f79a3d741c51fce52945221df8adcc3fb1b`
  - `test_monitoring_ai_service.py`:
    `0021244e30eab4f9ded74d39114d2c498dc43707dc2ae40ffa6d8c81b4030c0e`
  - `test_monitoring_protocol_preparation.py`:
    `d0f540980f01fb722c38c9cfcaf4d60831e7358a6e02a589664b404609fb6689`
  - `test_monitoring_ai_api.py`:
    `db209f15b4af69958d9bb50ff516680740ac20302d3a72afef9e142357644a80`

## Scope

- In scope:
  1. Bump protocol-clause prompt identity from v6 to
     `monitoring-protocol-clause-structuring-v7`; add v6 to the explicit terminal
     legacy set without changing active/stale cutover semantics.
  2. For `visit_window_and_order`, use a field-aware full topic-boundary view that
     detects IP/CM administration and first-dose language, informed-consent
     withdrawal variants, and distributed AE/CM collection wording.
  3. Keep false-positive controls: timing-only phrases such as “给药前7天内完成计划访视”
     are visit schedule/window, not an administration directive; “末次给药后28天进行
     安全性随访” fails as safety follow-up, not as first-dose administration.
  4. Count visit action families only from operative content: candidate title/text,
     normalized subject scope, conditions, time windows, thresholds, exceptions,
     required actions and claim text. Exclude claim uncertainty and user_action.
     Prevent `计划外访视安排` from matching both schedule and unscheduled.
  5. Preserve fail-closed atomicity: operative schedule/window plus operative
     rescheduling must be split and rejected when combined; pure schedule, pure
     reschedule and pure unscheduled must each pass the family gate.
  6. Before the single controlled repair, aggregate deterministic protocol validation
     failures across all provider candidates with stable candidate index/title and
     ordered errors. Whole-response persistence remains atomic: any invalid
     candidate means zero candidates. Do not weaken schema, structure, claim-anchor,
     conflict, evidence, language or generic validation.
  7. Strengthen the provider-visible protocol instruction and repair constraint to
     state the visit whitelist, forbidden topic content, one-operative-family rule
     and required splitting.
  8. Add complete focused tests for the v6 reviewer matrix and prompt/legacy cutover.
- Writable paths only:
  - `services/api/app/monitoring_ai_service.py`
  - `services/api/app/monitoring_protocol_preparation_service.py`
  - `tests/test_monitoring_ai_service.py`
  - `tests/test_monitoring_protocol_preparation.py`
  - `tests/test_monitoring_ai_api.py`
- Out of scope:
  - evidence packet v3 or structural repair v2 changes;
  - product APIs, startup scripts, `main.py`, frontend, browser or runtime DBs;
  - services/ports 8911 and 5174;
  - RUX/MY009/three-real-project execution;
  - candidate accept/reject/adopt/confirm/activate;
  - medical-writing business source;
  - v6 retry/reuse or prose salvage.

## Success Criteria

- Prompt is exactly v7 and v3-v6 terminal jobs remain visible through the explicit
  legacy set; active legacy work remains fail-closed.
- First-dose/IP and CM administration directives fail before family validation.
- Timing-only false-positive controls behave as specified.
- `撤回知情同意` and distributed “询问并记录……AE、合并用药” fail at the correct
  topic boundary.
- Family classification is operative-only and yields exactly one family for valid
  pure fixtures; combined schedule/reschedule rejects.
- A multi-candidate invalid output sends the only repair a complete,
  candidate-indexed deterministic error list; the repair count stays exactly one,
  and mixed valid/invalid output never partially persists.
- Exact C1-C5-shaped regression fixtures have the expected first/ordered failures.
- Existing packet-v3/list/table/conflict/50-ID and legacy-history tests remain green.
- Focused tests and `py_compile` pass. Codex later owns broader monitoring and
  medical-writing adjacent regression.

## Risk Boundaries

- Do not read/write runtime databases, backups or external production paths.
- Do not start services, call product/provider APIs, run real projects or make
  candidate decisions.
- Modify only the five explicitly writable files. Preserve all unrelated edits.
- Do not weaken a fail-closed gate merely to make a fixture pass.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- Launch the declared Pi route once and let the runner hard-wait up to 120 minutes;
  do not fixed-interval poll, re-dispatch or intervene for latency.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-01 04:29:19: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-01: Re-anchored from the v6 failed-closed review and pause. Global and
  workspace AGENTS hashes unchanged; all five writable baselines match; 8911/5174
  have zero listeners. No external discovery is needed because this is a bounded
  correction against immutable local runtime evidence and existing contracts.
- 2026-08-01: Pi/deepseek session `019fb9e0-eb37-7000-98a3-8c186dc03b89`
  completed the v7 architecture and two same-session recovery passes. It modified
  only authorized paths, but disclosed read-only inspection of three supporting
  implementation files beyond the explicit read list; no unauthorized writes or
  runtime actions were observed.
- 2026-08-01: Luna's first and second read-only reviews returned REVISE for ordinary
  lexical gaps. The declared native Codex fallback changed only
  `monitoring_ai_service.py` and `test_monitoring_ai_service.py`, closing oral
  medication/research-treatment, stop-participation/contact-loss, lowercase AE/CM,
  CMV exclusion, temporary/reschedule, and dose-time/day controls.
- 2026-08-01: Final Codex verification passed: compile; focused `336 passed`;
  medical-writing adjacent `200 passed`; full monitoring `1331 passed,
  4299 deselected, 27 warnings, 0 failed`. The broad selector includes offline
  frozen real-source-shape tests, but did not execute project workflows, create
  jobs/candidates, or call providers. 8911/5174 remained stopped.
- 2026-08-01: Same Luna session final recheck PASS. Offline v7 corrective is
  accepted. Next gate is at most one deliberately started, new-ID RUX v7
  `visit_window_and_order` canary with no v6 retry/reuse and explicit observation
  of the recorded adjacent lexical variants. MY009 remains blocked.
