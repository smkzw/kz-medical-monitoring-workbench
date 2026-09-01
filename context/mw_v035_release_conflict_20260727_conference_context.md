# Conference Context: mw_v035_release_conflict_20260727

Created: 2026-07-27 03:31:36
Objective: Review only new release conflicts: DeepSeek Flash-to-Pro translation support escalation identity, user-test project cleanup safety, and minimal medical-writer UI acceptance after live runtime re-entry
Task type: `complex_delivery_conference`
Risk: `critical`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

    - Visual/design/HTML/PPT tasks use a Codex-led panel with no sub-venue chair: Pi/Oh My Pi `kimi-code/k3` (high). If unavailable, the runner tries Cursor CLI `cursor-grok-4.5-high`, then Grok Build `grok-4.5`, then Kimi Code `k3`.
- Chinese labels or Chinese sentence review is handled directly by Codex and does not start a conference.
    - Other complex tasks use Pi/Alibaba `qwen3.8-max-preview` (xhigh) as the sub-venue chair, leading Pi `aishuo / cms-model` and CodeBuddy CLI `deepseek-v4-pro`. The chair fallback is Cursor CLI `cursor-grok-4.5-high`, then Cursor CLI `auto`.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Source Of Truth

- `services/api/app/writing_reference_upper_layer_adapters.py`
- `services/api/app/writing_reference_upper_layer_execution.py`
- `services/api/app/ai_role_runtime_settings.py`
- `tests/test_writing_reference_upper_layer_production_wiring.py`
- `scripts/maintenance/purge_user_test_projects.py`
- `records/archives/test_project_cleanup_20260727/user_test_projects_20260726T192857Z/purge_manifest.json`
- `evidence/mw_real_translation_protocol_20260726/v029_real_chain_20260727_result.json`
- `evidence/mw_real_translation_protocol_20260726/v034_real_chain_20260727_events.jsonl`
- `evidence/mw_real_translation_protocol_20260726/v035_pro_route_retry_20260727_events.jsonl` when available
- `.playwright-cli/page-2026-07-26T19-21-16-089Z.yml`
- `/tmp/mw_live_20260727.png` is visual evidence for Codex only; non-visual participants should use the accessibility snapshot and must not claim visual acceptance.

## Scope

- In scope: independently challenge the new Flash-to-Pro routing fix, prove whether runtime identity can actually become `deepseek-v4-pro`, inspect whether cleanup removed user-visible test state without deleting immutable audit history or reusable reference artifacts, and identify only high-impact UI conflicts visible in the supplied runtime snapshot.
- Out of scope: broad codebase audit, security/backdoor review, deletion of immutable audit records, rewriting the whole frontend, substitution of participant model output for the product's independently configured AI, and final release acceptance.

## Success Criteria

- Each selected primary route returns an auditable output or an explicit health/fallback reason.
- A reviewer can distinguish the previously invalid Flash-to-Flash escalation from the corrected Flash-to-Pro route using persisted requested/response model evidence.
- Cleanup evidence shows the project catalog reduced from 179 total entries (7 static + 172 user-created) to the 7 static projects while retaining recoverable compressed database backups and immutable audit rows.
- UI findings are limited to decisions that materially affect a lazy expert medical writer; logging, audit and low-value warnings are not proposed as persistent editor content.
- The prompt uses the correct Agent identity, provider/model, effort, tools-enabled policy, and same-session continuation policy.
- The runner records session, usage/tool observations, fallback decisions, and failure reasons without `--max-turns 1`.
- No production path is read or modified; Codex retains final acceptance.
- Participants may read the explicitly listed local runtime evidence but must not edit application source or runtime databases.

## Parallel Work Rule

For logic-heavy, rigor-sensitive, or artifact-heavy tasks, each participant independently runs the whole bounded workflow and writes a separate output. Leads compare after all available participant outputs are in or explicitly marked pending.

## Timeout Policy

- Participant soft wait: 60 minutes.
- Large-task participant wait: 120 minutes.
- Chair hard wait: 240 minutes.
- Failure rule: Do not fail a model for slow response alone; fail only on terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no useful progress after the high-budget same-session recovery loop. If a resumable session exists after a step/size boundary, continue it before fallback; repeated identical output/tool evidence triggers the no-progress breaker.
- Pass/turn boundary: one conference prompt is one conference pass. The
  `--max-turns` value controls internal Agent tool-calling turns and is never
  set to 1 for substantive conference execution; generated participant and
  chair commands use the route budgets recorded by the guard.

## Risk Boundaries

- External Agents are advisory; Codex remains final authority.
- Codex owns visual/browser/PPT/PDF/rendered checks, live authority checks, final clinical/regulatory conclusions, and production writes.
- Do not mark a slow model failed solely due to latency.
- Beijing time is within the `00:00-08:30` Aishuo blackout. The runner must record replacement of the Aishuo participant with its declared non-Aishuo route; any actual Aishuo call is invalid.
- `hy-MT3` is a historical typo. Do not reintroduce or recommend it; the only body translator in this task is runtime-owned Hy-MT2.

## Loop Log

- 2026-07-27 03:31:36: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-07-27 03:33: Source list, runtime evidence, Aishuo blackout, and conflict-only review boundary added by Codex.
