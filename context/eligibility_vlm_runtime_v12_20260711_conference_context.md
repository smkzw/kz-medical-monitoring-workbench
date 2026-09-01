# Conference Context: eligibility_vlm_runtime_v12_20260711

Created: 2026-07-12 00:02:39
Objective: Review the additive SQLite v12 durable VLM runtime foundation, identify remaining release-blocking defects, and define the next bounded circuit/identity slice without opening production VLM or using real clinical images.
Task type: `complex_delivery_conference`
Risk: `high`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Hermes And Reasonix Delegation

- Lead/chair: Hermes custom provider `aishuo` / `MiniMax-M3`, per the user's current project-wide routing rule.
- Hermes participant models: OpenCode Go `qwen3.7-plus` and OpenCode Go `mimo-v2.5`, all default reasoning effort unless Codex overrides.
- Reasonix CLI participant model: `deepseek-flash` alias for `deepseek-v4-flash`.
- All `deepseek-v4-flash` and `deepseek-v4-pro` routes must leave Hermes and run through Reasonix CLI. OpenCode Go, Hermes custom providers, and the direct DeepSeek provider are not allowed for these models in this workflow.
- `qwen3.7-plus` must be smoke-tested in this route because it recently had intermittent run errors.
- Main-venue high-risk reviewer: Reasonix CLI `deepseek-pro` alias for `deepseek-v4-pro` only. Hermes/OpenCode Go/direct DeepSeek routes are not allowed for this role.
- Google Antigravity CLI `Gemini 3.5 Flash (Medium)` is the visual sub-venue chair for visual conferences and an independent participant in other conferences.
- The Antigravity visual chair is advisory; Codex retains final pixel-level/browser/PPT/PDF/image acceptance.

## Source Of Truth

- `services/api/app/sqlite_runtime_store.py`
- `services/api/app/eligibility_evidence_worker.py`
- `services/api/app/eligibility_evidence_tasks.py`
- `services/api/app/vlm_gateway.py`
- `tests/test_eligibility_vlm_runtime.py`
- `records/active_slices/eligibility_next_slice_20260711/VLM_DURABLE_RUNTIME_V12.md`
- `runs/subagents/20260711_vlm_runtime_v12/review_summary.md`

## Scope

- In scope: transaction, migration, lease fencing, server-owned provenance, privacy, public projection, fail-closed behavior, and the smallest next durable circuit/identity slice.
- Out of scope: real clinical images, production model enablement, clinical conclusions, UI/visual work, live web research, and edits by delegated agents.

## Success Criteria

- Identify any remaining reproducible P0/P1 defect in the bounded v12 implementation.
- Distinguish defects fixed in this slice from release gates intentionally still closed.
- Confirm that no path creates evidence spans, visual-QC pass, eligibility decisions or medical approval from a VLM descriptor.
- Recommend a bounded next implementation slice for durable multi-process circuit state and production identity without opening production VLM.
- Hermes chair must run on verified `aishuo/MiniMax-M3`; no silent fallback.

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

- 2026-07-12 00:02:39: Conference initialized by `hermes_workflow_guard.py init-conference`.
