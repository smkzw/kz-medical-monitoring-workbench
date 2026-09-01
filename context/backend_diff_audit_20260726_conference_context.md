# Conference Context: backend_diff_audit_20260726

Created: 2026-07-26 12:50:26
Objective: Audit backend and contract differences against the pre-takeover baseline without modifying product code; produce evidence-backed findings in the designated handoff report
Task type: `complex_delivery_conference`
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

- User-authorized current workspace:
  `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench`.
- Pre-takeover baseline:
  `/tmp/mw_agent1_baseline_20260725_retake1`.
- Takeover records:
  `records/handoffs/CODEX_RESUME_P0_18_20260726.md`,
  `records/handoffs/codex_retake_20260726/00_AUDIT_JOURNAL.md`,
  `01_RECONSTRUCTED_DIFF_SUMMARY.md`, and
  `02_EXACT_TAKEOVER_INVENTORY_DIFF.md`.
- Exact audit surface: `packages/contracts/workbench_contracts/models.py`;
  every modified file under `services/api/app`; and the four 2026-07-26
  additions `medical_writing_chinadrugtrials_client.py`,
  `medical_writing_condition_term_resolver.py`,
  `medical_writing_research_pipeline.py`, and
  `workbench_notifications.py`.
- Current filesystem and reproducible focused checks override historical PASS
  claims. Existing reports are leads only.

## Scope

- In scope: backend/contract differential audit for real functional bugs,
  cross-module contract conflicts, state-machine defects, indication/phase/
  route hard-coding or overfitting, AI prompt/source-gate defects, and
  concurrency/idempotency/failure-recovery defects.
- In scope: read-only/static inspection and non-destructive focused tests.
- In scope output:
  `records/handoffs/codex_retake_20260726/evidence/SUBAGENT_BACKEND_DIFF_AUDIT.md`.
- Out of scope: product-code edits, broad product acceptance, frontend visual
  review, security-backdoor audit, speculative findings without evidence, and
  external network discovery.

## Success Criteria

- Every target file is diffed against the supplied baseline and reviewed in
  current call context.
- Every reported P0-P3 finding includes current file and line, a reproduction
  or concrete failure path, why existing tests missed it, a bounded fix, and a
  minimal regression test.
- Claims without reproducible/static evidence are excluded.
- Product code is not modified. Only audit/process records may be written.
- Selected conference routes return auditable objections or explicit
  health/fallback reasons; Codex independently verifies every retained finding.

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
- Do not modify files under `packages/`, `services/`, `frontend/`, `scripts/`,
  or `tests/`.
- Do not perform a security-backdoor audit.

## Loop Log

- 2026-07-26 12:50:26: Conference initialized by `hermes_workflow_guard.py init-conference`.
