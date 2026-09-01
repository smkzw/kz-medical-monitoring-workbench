# Conference Context: mw_ai_first_corpus_prefill_runtime_challenge_20260801

Created: 2026-08-01 14:34:15
Objective: 只读反证审阅AI-first Protocol corpus prefill最终r4实现、真实浏览器证据与唯一SQLite差异，判定是否存在P0-P4问题
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

- Global and workspace `AGENTS.md`.
- Final runtime task records:
  - `context/mw_ai_first_corpus_prefill_runtime_20260801_context.md`
  - `runs/pi_mw_ai_first_corpus_prefill_runtime_20260801.md`
  - `reviews/codex_mw_ai_first_corpus_prefill_runtime_20260801_review.md`
  - `metrics/mw_ai_first_corpus_prefill_runtime_20260801_metrics.md`
- Final implementation:
  - `services/api/app/medical_writing_authoring_prefill_ai.py`
  - `services/api/app/medical_writing_authoring_prefill_evidence_binding.py`
  - `services/api/app/medical_writing_authoring_prefill_corpus_bridge.py`
  - `services/api/app/medical_writing_authoring_prefill_evidence.py`
  - `services/api/app/medical_writing_authoring_prefill.py`
  - `tests/test_medical_writing_authoring_prefill_corpus_bridge.py`
- Read-only final clone:
  `/tmp/mw-ai-first-prefill-runtime-r4-1eQtHYQD`.
- Read-only source baseline:
  `/private/var/folders/yb/31r9763x6_54mdxswxk36c4w0000gn/T/mw-phase0b-browser-rwanbzol/runtime_glm_retest4`.
- Current filesystem and SQLite logical state are final truth. The user has
  explicitly authorized these two runtime paths for this medical-writing task.

## Scope

- In scope:
  - read-only code and focused-test audit;
  - read-only verification of the final r4 authoring journey/event delta;
  - review of the recorded Computer Use browser evidence;
  - severity assignment P0-P4 for source-binding, exact-fact quarantine,
    projection order, deterministic fallback, evidence-gap accuracy,
    repeated source display, idempotency, and adoption safety;
  - concrete bounded remediation if a defect is found.
- Out of scope:
  - modifying any product source, test, SQLite, runtime, or monitoring file;
  - starting/stopping/restarting services;
  - rerunning tests or model generation;
  - clicking the UI, adopting a candidate, OCR, translation, triage,
    preparation, Synopsis, CSR, Word, or release-matrix testing;
  - reading other participant outputs before the chair synthesis.

## Success Criteria

- Each selected primary route returns an auditable output or an explicit health/fallback reason.
- The prompt uses the correct Agent identity, provider/model, effort, tools-enabled policy, and same-session continuation policy.
- The runner records session, usage/tool observations, fallback decisions, and failure reasons without `--max-turns 1`.
- The reviewer confirms or disproves that exactly three explicitly quoted
  Protocol terms can be surfaced only as pending/manual competitor options,
  while the other ten design values remain empty.
- The reviewer independently checks that competitor evidence cannot become a
  current-project fact and that invalid/stale/unbound evidence fails closed.
- The reviewer checks the recorded source/clone delta and identifies any
  unsupported leap in the “one event only / no upstream writes” conclusion.
- Every P0-P4 finding has an exact locator, failure mode, user consequence,
  and smallest safe correction; a no-issue conclusion states the audited
  scope and residual risk.
- The authorized runtime paths are read-only; nothing is modified. Codex
  retains final acceptance.

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
- Do not inspect or alter medical-monitoring files; they are a concurrent
  user-owned lane.
- Do not treat transport success, test pass count, model confidence, or the
  reviewer report as final runtime acceptance.
- The latest OCR correction is context only: future not-yet-started files use
  official `PaddleOCR-VL-1.6`; GLM-started files finish with GLM. This review
  must not run OCR.

## Loop Log

- 2026-08-01 14:34:15: Conference initialized by `hermes_workflow_guard.py init-conference`.
