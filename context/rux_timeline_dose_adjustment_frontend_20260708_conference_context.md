# Conference Context: rux_timeline_dose_adjustment_frontend_20260708

Created: 2026-07-08 12:35:22
Objective: Review and decide the minimal frontend design/implementation for RUX Subject Timeline dose_adjustment events. GLM-5.2 and Kimi focus on clinical UX/frontend, DeepSeek Pro focuses on Chinese clinical terminology and risk wording. No source edits by Hermes.
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

- User instructions in the current Codex thread and durable logs, especially `logs/SOFT_PAUSE_20260708_1216_CST.md`.
- `frontend/AGENTS.md` for Subject Timeline visual contract and module naming/source-boundary rules.
- `context/rux_timeline_dose_adjustment_frontend_20260708_review_packet.md` for current-code excerpts and decision questions.
- `frontend/src/App.jsx` for current implementation when assigned to frontend reviewer.
- `research/rux_timeline_dose_adjustment_interaction_research_20260708.md` for external product/open-source design evidence.
- Backend accepted behavior is recorded in `reviews/codex_rux_inbox_patch_review_20260708_review.md` and `tests/test_rux_monitoring_service.py`: RUX ECB dose pause/restart events are now `dose_adjustment`.

## Scope

- In scope:
  - decide minimal Subject Timeline frontend mapping for `dose_adjustment`;
  - decide Chinese label, compact event prefix, lane assignment, and risk tone;
  - define narrow tests and browser/QC checks for Codex.
- Out of scope:
  - broad redesign of 医学监查;
  - full RUX project selector/dashboard integration;
  - Patient Profile chart generation beyond avoiding misleading wording;
  - production code edits by Hermes;
  - final browser/visual acceptance by Hermes.

## Success Criteria

- At least GLM-5.2, Kimi k2.7 code, and DeepSeek Pro have produced bounded advisory outputs or route failures are recorded.
- Codex can make a documented decision on lane, label, prefix, tone, and minimal UI scope.
- Any production code change must follow TDD: write failing test, observe failure, patch minimally, rerun focused and relevant broader verification.
- Records must state what is accepted now and what remains deferred.

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

- 2026-07-08 12:35:22: Conference initialized by `hermes_workflow_guard.py init-conference`.
