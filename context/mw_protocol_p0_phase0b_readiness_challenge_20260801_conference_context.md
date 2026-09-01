# Conference Context: mw_protocol_p0_phase0b_readiness_challenge_20260801

Created: 2026-08-01 08:59:05
Objective: Independently challenge the Protocol P0 Phase 0B typed drafting readiness slice for blank-draft compatibility, fail-closed clinical semantics, AI-first UX, idempotency, and medical-monitoring boundary preservation
Task type: `code_open_audit`
Risk: `high`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

    - Visual/design/HTML/PPT tasks use a Codex-led panel with no sub-venue chair: Pi/Oh My Pi `kimi-code/k3-256k` (high). If unavailable, the runner tries Cursor CLI `cursor-grok-4.5-high`, then Grok Build `grok-4.5`, then Kimi Code `k3-256k`.
- Chinese labels or Chinese sentence review is handled directly by Codex and does not start a conference.
    - Other complex tasks use Pi/Alibaba `qwen3.8-max-preview` (xhigh) as the sub-venue chair, leading Codex subAgent `gpt-5.6-luna` (max) and Pi/DeepSeek `deepseek-v4-flash` (max). In Codex App, the Codex subAgent participant is dispatched natively through `multi_agent_v1` so the parent can see progress and reuse the same session. The Codex participant fallback chain is Kimi K3 high -> Pi/DeepSeek V4 Flash max -> CodeBuddy hy3 max. Chair fallback is Grok Build `grok-4.5`, then Cursor CLI `cursor-grok-4.5-high`.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Source Of Truth

- Parent task context and evidence:
  `context/mw_protocol_p0_phase0b_rebaseline_20260801_context.md`,
  `reviews/codex_mw_protocol_p0_phase0b_rebaseline_20260801_review.md`,
  and `metrics/mw_protocol_p0_phase0b_rebaseline_20260801_metrics.md`.
- Authorized read-only implementation set:
  - `packages/contracts/workbench_contracts/models.py`
  - `services/api/app/medical_writing_protocol_template.py`
  - `services/api/app/medical_writing_greenfield.py`
  - `services/api/app/medical_writing.py`
  - `services/api/app/ai_task_runner.py`
  - `tests/test_medical_writing_protocol_template.py`
  - targeted blank-greenfield test evidence in
    `tests/test_medical_writing_greenfield_runtime.py`
  - `frontend/src/App.jsx`, `frontend/src/styles.css`, and
    `frontend/AGENTS.md`.
- Official ICH M11 Step 4 final guideline/template URLs recorded in the parent
  context. No external executable candidate is under consideration.
- Current filesystem is final truth. This is a non-git shared tree; file
  hashes before and after the bounded change are recorded in the parent
  context.

## Scope

- In scope:
  - Read-only contradiction review of the six connected changed files and
    focused tests/build evidence.
  - Determine whether `blocked_missing_inputs` or empty-block normalization
    breaks the existing blank greenfield AI drafting/apply path.
  - Challenge structural-content/container classification, fail-closed
    blocker validation, legacy payload compatibility, idempotency, and
    project isolation.
  - Challenge whether the compact `AI 先起草` surface truly keeps the user in
    a reviewer role and whether missing-input expansion is understandable.
  - Return delta-only P0-P4 findings with exact file/line evidence, no-issue
    scope, recheck targets, and a READY/REVISE recommendation.
- Out of scope:
  - Any source/test/config/database/runtime edit by participants or chair.
  - Starting services, importing full `main:app`, browser/Word/model runtime,
    touching medical-monitoring files, or replaying frozen r42 work.
  - Synopsis, CSR, Protocol Phase 0C/0D, release promotion, and the final
    multi-route E2E loop.

## Success Criteria

- Each selected primary route returns an auditable output or an explicit health/fallback reason.
- The prompt uses the correct Agent identity, provider/model, effort, tools-enabled policy, and same-session continuation policy.
- The runner records session, usage/tool observations, fallback decisions, and failure reasons without `--max-turns 1`.
- No path is modified by the reviewers; Codex retains final acceptance.
- Every finding has severity, exact locator, failure mechanism, and bounded
  remediation. A no-issue claim identifies the exact path and evidence
  inspected.
- Recommendation is `READY` only if the existing blank-draft path remains
  reachable and no P0-P2 defect remains in this bounded slice.

## Parallel Work Rule

For logic-heavy, rigor-sensitive, or artifact-heavy tasks, each participant independently runs the whole bounded workflow and writes a separate output. Leads compare after all available participant outputs are in or explicitly marked pending.

## Timeout Policy

- Participant soft wait: 60 minutes.
- Large-task participant wait: 120 minutes.
- Chair hard wait: 120 minutes.
- Failure rule: Do not fail a model for slow response alone; fail only on terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no useful progress after the high-budget same-session recovery loop. If a resumable session exists after a step/size boundary, continue it before fallback; repeated identical output/tool evidence triggers the no-progress breaker.
- Pass/turn boundary: one conference prompt is one conference pass. The
  `--max-turns` value controls internal Agent tool-calling turns and is never
  set to 1 for substantive conference execution; generated participant and
  chair commands use the route budgets recorded by the guard.

## Risk Boundaries

- External Agents are advisory; Codex remains final authority.
- Codex owns visual/browser/PPT/PDF/rendered checks, live authority checks, final clinical/regulatory conclusions, and production writes.
- Do not mark a slow model failed solely due to latency.
- Medical-monitoring files and runtime state are excluded even though they
  share the workbench.
- The conference may read the authorized product paths above but must not
  write them or run the full application.

## Loop Log

- 2026-08-01 08:59:05: Conference initialized by `hermes_workflow_guard.py init-conference`.
- Prompt preflight initially failed because the guard-generated hard boundary
  embedded the workspace as a production-like absolute path. The three
  prompts were corrected to use current workspace `.`; all three preflights
  then passed with no warnings or errors.
- Native Codex App dispatch metadata requires exact
  `codex/gpt-5.6-luna/max`, but the callable native collaboration interface
  in this task exposes only `gpt-5.6-sol` and `gpt-5.6-terra` overrides.
  Substituting either would silently change the declared route, so the
  guard-generated `codex-subagent/gpt-5.6-luna/max` CLI compatibility runner
  is authorized for this conference pass. This is recorded as
  `cli_compatibility_fallback_model_selector_unavailable`, not the native
  production default.
- Both participants completed one terminal-success pass with their declared
  primary models and no fallback. The guard-generated chair command then
  failed before session creation because the installed
  `conference_session_runner.py` does not accept its emitted
  `--participant-stdout` arguments. Those arguments are redundant because
  the chair prompt already declares both runner-owned participant reports as
  its read set. The bounded recovery is to remove only those unsupported
  arguments and launch the same chair/provider/model/prompt once.
- The chair reused session `019fbae4-9d32-7000-be7e-534f120397f9`.
  Runner-owned stdout is authoritative for `round_count=2`; the final chair
  report's “four rounds” language describes its own review-pass narrative and
  is not used as runner round evidence.
- Boundary deviation discovered during Codex final acceptance:
  `tests/test_medical_writing_greenfield_runtime.py` imports
  `services.api.app.main as app_main` at line 72. The chair report both
  claimed it executed that 18-test module and claimed no `main:app` import;
  those claims are contradictory, and the no-main/no-monitoring claim is
  rejected.
- Monitoring forensic result:
  - all four stores return `integrity_check=ok`;
  - assurance is logically identical to the old r42 snapshot;
  - AI, batches, and daily-runs are not globally identical in schema and/or
    rows, with concurrent monitoring activity visible through 09:10:55 CST;
  - without an immediate pre-conference snapshot, the import's exact logical
    contribution cannot be separated from the concurrent monitoring lane;
  - read-only SQLite inspection refreshed SHM physical metadata/mtime but did
    not write logical data.
- Conference acceptance is therefore limited to the seven-file offline
  Protocol readiness/aggregation slice. The conference did not satisfy its
  monitoring boundary, and no runtime/browser/product-model/Word acceptance
  is inferred.
