# Conference Context: mw-r14-triage-parent-timeout

Created: 2026-07-29 04:59:18
Objective: Choose the smallest reliable repair for the medical-writing research pipeline parent 900-second timeout while a live competitor-triage child continues progressing; preserve durable recovery, truthful progress, and the serial E2E matrix
Task type: `high_risk_contradiction_review`
Risk: `high`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

    - Visual/design/HTML/PPT tasks use a Codex-led panel with no sub-venue chair: Pi/Oh My Pi `kimi-code/k3-256k` (high). If unavailable, the runner tries Cursor CLI `cursor-grok-4.5-high`, then Grok Build `grok-4.5`, then Kimi Code `k3-256k`.
- Chinese labels or Chinese sentence review is handled directly by Codex and does not start a conference.
    - Other complex tasks use Pi/Alibaba `qwen3.8-max-preview` (xhigh) as the sub-venue chair, leading Pi `aishuo / cms-model` and CodeBuddy CLI `deepseek-v4-pro`. The chair fallback is Cursor CLI `cursor-grok-4.5-high`, then Cursor CLI `auto`.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Source Of Truth

- `context/mw_final_5x3_release_r14_20260729_context.md`
- `runs/execution/mw_final_5x3_harness_20260728/rounds/release-r14-20260729/slots/A1/lazy_medical_writer/DEFECTS.md`
- `runs/execution/mw_final_5x3_harness_20260728/rounds/release-r14-20260729/slots/A1/lazy_medical_writer/BROWSER_ACTION_TRACE.json`
- `runs/execution/mw_final_5x3_harness_20260728/rounds/release-r14-20260729/slots/A1/lazy_medical_writer/service_evidence/database_at_blocker.txt`
- `services/api/app/medical_writing_research_pipeline.py`
- `services/api/app/medical_writing_durable_jobs.py`
- `services/api/app/medical_writing_competitor_triage.py`
- `tests/test_mw_triage_deadline_reconcile_r10.py`
- `tests/test_medical_writing_research_pipeline_progress.py`
- AWS Step Functions official heartbeat semantics:
  `https://docs.aws.amazon.com/step-functions/latest/apireference/API_SendTaskHeartbeat.html`
- AWS Step Functions official activity guidance:
  `https://docs.aws.amazon.com/step-functions/latest/dg/concepts-activities.html`

## Scope

- In scope: independently diagnose the parent/child timeout and retry-state
  contradiction; compare a larger fixed timeout, progress/liveness-aware
  waiting with a hard ceiling, and event-driven parent continuation; recommend
  the smallest reliable route and precise regression gates.
- In scope: preserve truthful granular progress, current durable claim/lease
  semantics, idempotency, old-owner isolation, graceful shutdown recovery, and
  no duplicate independent-AI work.
- Out of scope: editing product source, changing the 5x3 clinical scenarios,
  bypassing corpus gates, or treating skeleton content as acceptance.

## Success Criteria

- Each selected primary route returns an auditable output or an explicit health/fallback reason.
- Recommendation identifies the exact failure mechanism and distinguishes
  liveness heartbeats from business progress.
- Recommendation covers the case observed in r14: a 15-batch external-AI child
  is still live and progressing after the parent's fixed 900-second wait.
- Recommendation states whether this is a common prerequisite defect that
  should be repaired before the remaining serial E2E slots.
- Verification plan includes slow-call timing, progress monotonicity,
  parent/child terminal consistency, retry/restart, graceful shutdown,
  idempotency, and stale-owner cases.
- The prompt uses the correct Agent identity, provider/model, effort, tools-enabled policy, and same-session continuation policy.
- The runner records session, usage/tool observations, fallback decisions, and failure reasons without `--max-turns 1`.
- No production path is read or modified; Codex retains final acceptance.

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

## Loop Log

- 2026-07-29 04:59:18: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-07-29 05:00 Beijing: the generated aishuo participant route was
  prohibited by the 00:00-08:30 Beijing window. It is replaced for this pass
  by `Kimi Code / kimi-code / k3-256k` high so the Qwen chair remains an
  independent route. The CodeBuddy DeepSeek V4 Pro participant is unchanged.
