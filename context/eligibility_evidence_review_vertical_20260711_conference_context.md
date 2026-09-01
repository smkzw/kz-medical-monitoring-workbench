# Conference Context: eligibility_evidence_review_vertical_20260711

Created: 2026-07-11 12:31:48
Objective: 设计并评审D001与MY009真实原始资料从OCR/文本证据到逐条IN/EX独立AI初审、医学确认和审计持久化的生产级垂直切片
Task type: `complex_delivery_conference`
Risk: `critical`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Hermes And Reasonix Delegation

- Lead/chair: OpenCode Go `minimax-m3`.
- Hermes participant models: OpenCode Go `qwen3.7-plus` and OpenCode Go `mimo-v2.5`, all default reasoning effort unless Codex overrides.
- Reasonix CLI participant model: `deepseek-flash` alias for `deepseek-v4-flash`.
- All `deepseek-v4-flash` and `deepseek-v4-pro` routes must leave Hermes and run through Reasonix CLI. OpenCode Go, Hermes custom providers, and the direct DeepSeek provider are not allowed for these models in this workflow.
- `qwen3.7-plus` must be smoke-tested in this route because it recently had intermittent run errors.
- Main-venue high-risk reviewer: Reasonix CLI `deepseek-pro` alias for `deepseek-v4-pro` only. Hermes/OpenCode Go/direct DeepSeek routes are not allowed for this role.

## Source Of Truth

- `records/active_slices/eligibility_next_slice_20260711/CONFERENCE_SOURCE_PACKET.md`
- `records/active_slices/eligibility_next_slice_20260711/INDEPENDENT_BACKEND_AUDIT.md`
- `records/active_slices/eligibility_next_slice_20260711/INDEPENDENT_FRONTEND_AUDIT.md`
- `logs/subsystems/eligibility_review_log.md`
- `services/api/app/eligibility_protocol_rules.py`
- `services/api/app/eligibility_raw_intake.py`
- `services/api/app/ai_gateway.py`
- `services/api/app/ai_task_runner.py`
- `services/api/app/source_intake.py`
- `services/api/app/sqlite_runtime_store.py`
- `packages/contracts/workbench_contracts/models.py`
- `frontend/src/App.jsx` eligibility section only
- `frontend/src/styles.css` eligibility section only
- `frontend/tests/eligibility_real_projects_qc.mjs`
- Do not read raw patient files, legacy enrollment-review outputs, runtime secrets, or production SQLite in this advisory conference.

## Scope

- In scope: source/revision identity, OCR evidence spans, task-specific AI schema, medical review state machine, SQLite persistence, API contracts, desktop interaction, six-subject real-project test matrix, stale-source and cross-project gates.
- Out of scope: production edits, raw patient file reading by conference models, whole 143-subject batch, formal eligibility approval/randomization release, archive auto-unpack, legacy conclusion migration, mobile optimization, dashboard projection.

## Success Criteria

- Produce an implementable architecture and bounded file/test plan.
- Explicitly resolve inclusion/exclusion decision semantics, source-traceability state, AI batching and partial-failure behavior.
- Prevent stale rules/files/evidence from being saved or displayed as current.
- Preserve PHI/path privacy and project isolation.
- Require independent OCR/LLM execution and no Codex fallback.
- Identify any issue that must block implementation rather than be deferred.

## Parallel Work Rule

For logic-heavy, rigor-sensitive, or artifact-heavy tasks, each participant independently runs the whole bounded workflow and writes a separate output. Leads compare after all available participant outputs are in or explicitly marked pending.

## Timeout Policy

- Participant soft wait: 20 minutes.
- Large-task participant wait: 45 minutes.
- Lead/main hard wait: 90 minutes.
- Failure rule: Do not fail a model for slow response alone; fail only on terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Risk Boundaries

- Hermes and Reasonix are advisory; Codex remains final authority.
- Codex owns visual/browser/PPT/PDF/rendered checks, live authority checks, final clinical/regulatory conclusions, and production writes.
- Do not mark a slow model failed solely due to latency.

## Loop Log

- 2026-07-11 12:31:48: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-07-11: Codex added the bounded source packet, independent backend audit and current code/test read list; no production edits authorized.
