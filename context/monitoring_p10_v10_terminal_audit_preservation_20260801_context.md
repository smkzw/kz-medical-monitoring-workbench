# Task Context: monitoring_p10_v10_terminal_audit_preservation_20260801

Created: 2026-08-01 15:37:43
Objective: Preserve terminal v9 job status, failure evidence, timestamps, attempts and candidates during v10 startup retirement while keeping v9 status-incompatible, non-retryable and non-reusable
Task type: `finite_code_task`
Risk: `high`
Selected agent route: `deepseek` / `deepseek-v4-flash` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Current filesystem and latest global/workbench instructions.
- Failed zero-submit clone:
  `runs/execution/monitoring_p10_v10_zero_submit_gate_20260801/runtime_zero_submit/medical_monitoring_ai.sqlite3`
  (read-only evidence).
- Fresh pre-start snapshot:
  `runs/execution/monitoring_p10_v10_zero_submit_gate_20260801/prestart_snapshot/medical_monitoring_ai.sqlite3`
  (read-only evidence).
- `context/monitoring_p10_v10_zero_submit_gate_20260801_context.md`
- `services/api/app/monitoring_ai_repository.py`
- `services/api/app/monitoring_protocol_preparation_service.py`
- `services/api/app/main.py`
- `tests/test_monitoring_ai_repository.py`
- `tests/test_monitoring_protocol_preparation.py`
- `tests/test_monitoring_ai_startup_recovery.py`

Observed defect:

- Before startup the frozen v9 job is
  `failed/invalid_ai_output`, retryable false, with original terminal
  `updated_at`, one attempt and zero candidates.
- v10 startup currently changes it to
  `stale_input/superseded_prompt_contract` and overwrites `updated_at`.
- Attempts and candidates remain unchanged, but the primary terminal failure
  evidence is no longer represented by the job row.
- Repository support already distinguishes terminal audit preservation from
  active-work retirement through `legacy_terminal_prompt_versions`; the defect
  is that one set is currently reused for both audit preservation and status
  compatibility.

External-discovery decision: no new web/package scan. This is a local contract
composition bug in already-reviewed repository primitives, with no dependency,
architecture or tool choice.

## Scope

- In scope:
  - introduce a distinct protocol retirement-audit prompt-version set that
    includes v9 for terminal preservation;
  - keep `PROTOCOL_STATUS_LEGACY_PROMPT_VERSIONS` unchanged so v9 remains
    status-incompatible under v10;
  - make startup pass the retirement-audit set to
    `supersede_prompt_versions_except`;
  - update focused tests so terminal completed/failed v9 rows retain status,
    failure fields, timestamps, attempts and candidates while gaining immutable
    retirement markers;
  - prove queued/running/blocked v9 still transition to stale, lose leases,
    reject late completion, cannot be claimed/retried/reused, and a distinct
    v10 job is selected.
- Out of scope:
  - unrelated generic repository semantics;
  - any service/provider/port/real-project/runtime mutation;
  - prompt v10 visit semantics or provider-only stable-ID migration;
  - medical-writing files or unrelated refactors.

## Success Criteria

- Terminal v9 completed/failed rows receive a durable
  `superseded_prompt_contract` retirement marker without changing status,
  failure code/message, retryable value, created/updated timestamps, attempt
  lineage or candidate status/content.
- v9 remains absent from the status-compatible legacy set and is never selected
  by protocol-preparation status/start under v10.
- Active v9 queued/running/blocked rows still become stale and non-retryable;
  late completion loses CAS and creates no candidate.
- Existing v3-v8 behavior remains unchanged.
- Focused repository/preparation/startup tests and adjacent monitoring AI/API
  regressions pass.

## Risk Boundaries

- Writable product paths are exactly:
  - `services/api/app/monitoring_ai_repository.py`
  - `services/api/app/monitoring_protocol_preparation_service.py`
  - `services/api/app/main.py`
  - `tests/test_monitoring_ai_repository.py`
  - `tests/test_monitoring_protocol_preparation.py`
  - `tests/test_monitoring_ai_startup_recovery.py`
- Frozen pre-edit hashes:
  - repository:
    `a6930192e70688de3b90cea7eedd0884a44d910e712225cd4d9f4f71f3fbeb0c`
  - service:
    `899d2b01d6df4a6efda5e02ac5697348d5f0514272c57f0a5f1af35e33a7ab00`
  - main:
    `aceb5b3b3383f9b73ceca891c4d9965449f855192101be19752c25816ccf1c28`
  - repository test:
    `7edca70ace3553d844f021a2102ec052ac24f8dbeba2111cc8d6be725ec6fece`
  - preparation test:
    `6496f4b5a563830127dfdd3ad1c73f1f76d9c489bc68a3927fffb50afa4e67e2`
  - startup test:
    `2b406c3445271986c289d54ae2cc48ada3dc44b34d42b942e69a6e521fe0d9bb`
- Stop before editing if any hash differs.
- Runtime evidence paths are read-only; use only temporary test databases.
- Do not start services, providers, browsers or real projects.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Dispatch the declared Pi/deepseek-v4-flash route once at max effort and wait
  on the runner hard wait up to 120 minutes.
- Do not fixed-interval poll, duplicate, interrupt or fallback because of
  latency. A same-session follow-up is allowed only after terminal output and a
  concrete acceptance gap.

## Loop Log

- 2026-08-01 15:37:43: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- The v10 zero-submit attempt was stopped before POST immediately after the
  terminal-audit overwrite was observed. 8911/5174 are stopped and the
  authoritative DB/WAL hashes remain unchanged.
- Pi initial pass stopped before editing because `main.py` changed after the
  original freeze. Codex inspected the current file: the concurrent change did
  not implement or overlap the target retirement-set wiring. The current
  filesystem is authoritative; the new main hash above is explicitly
  re-frozen, all current unrelated content must be preserved, and the same Pi
  session may perform one targeted completion pass.
- That completion pass implemented the status-set/retirement-audit-set split
  and passed Codex-direct `527 passed`. Luna then found a decisive P1 in the
  next propagation path: production v9 and v10 use the same business key, so
  `_create_job()` calls `supersede_business_key_except()` after startup and
  re-transitions the marker-preserved terminal v9 to stale, overwriting the
  very evidence startup preserved. The current test hid this with suffixed v9
  business keys and used a non-representative `provider_timeout` attempt.
- The second and final same-session recovery pass is authorized to:
  - make business-key supersession marker-only for completed/failed rows that
    already carry an immutable contract-retirement marker;
  - retain existing behavior for unmarked terminal rows and every active row;
  - add exact production-key failed-v9 coverage with
    `invalid_ai_output` / `invalid_output`, initial+repair response lineage and
    zero candidates;
  - add protocol-specific blocked-v9 coverage.
