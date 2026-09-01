# Conference Context: mw_translation_identity_v2_review_20260727

Created: 2026-07-27 01:44:09
Objective: Review only the post-fix translation immutable identity design: exact plan lookup, fingerprint-bound chunk identity, integration-bound translation/save identity, unchanged repository immutability, and focused regression evidence. Return only conflicts, missing tests, and residual release risks; do not modify source or runtime.
Task type: `high_risk_contradiction_review`
Risk: `high`
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

- `services/api/app/chapter_translation_pipeline.py`
- `services/api/app/writing_reference_translation_batch.py`
- `services/api/app/writing_reference_repository.py`
- `tests/test_mw_v11_translation_alignment.py`
- `tests/test_writing_reference_translation_batch.py`
- `tests/test_writing_reference_translation_durable_jobs.py`
- `evidence/mw_real_translation_protocol_20260726/v026_full_batch_final.json`
- `evidence/mw_real_translation_protocol_20260726/TRANSLATION_RERUN_PATH_REVIEW.md`
- `records/handoffs/codex_retake_20260726/00_AUDIT_JOURNAL.md`

## Scope

- In scope: exact contract-bound plan lookup; fingerprint-bound immutable chunk
  identity; integration-bound translation/save identity; unchanged repository
  conflict checks; focused regression completeness; post-fix live acceptance
  risks.
- Out of scope: source edits, DB edits, UI, translation wording quality,
  corpus admission, DOCX export, broad security audit, and re-review of
  unrelated completed work.

## Success Criteria

- Each selected primary route returns an auditable output or an explicit health/fallback reason.
- The prompt uses the correct Agent identity, provider/model, effort, tools-enabled policy, and same-session continuation policy.
- The runner records session, usage/tool observations, fallback decisions, and failure reasons without `--max-turns 1`.
- No source, runtime DB, batch or service is modified; Codex retains final
  acceptance.

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
- Beijing blackout is active. The original aishuo participant is replaced by
  Pi `opencode-go/deepseek-v4-flash`; original and effective routes must be
  recorded. No aishuo route or fallback may be dispatched before 08:30.

## Loop Log

- 2026-07-27 01:44:09: Conference initialized by `hermes_workflow_guard.py init-conference`.
