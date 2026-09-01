# Conference Context: mw_ai_first_prefill_postcorrective_runtime_challenge_20260801

Created: 2026-08-01 18:09:35
Objective: Independently challenge the post-corrective AI-first Protocol prefill source, deterministic tests, r6 real-browser evidence, exactly-once lineage, fail-closed adoption, and residual P0-P4 risk without modifying product or runtime state.
Task type: `high_risk_contradiction_review`
Risk: `high`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

    - Visual/design/HTML/PPT tasks use a Codex-led panel with no sub-venue chair: Pi/Oh My Pi `kimi-code/k3-256k` (high). If unavailable, the runner tries Cursor CLI `cursor-grok-4.5-high`, then Grok Build `grok-4.5`, then Kimi Code `k3-256k`.
- Chinese labels or Chinese sentence review is handled directly by Codex and does not start a conference.
    - Other complex tasks use Pi/Alibaba `qwen3.8-max-preview` (xhigh) as the sub-venue chair, leading Codex subAgent `gpt-5.6-luna` (max) and Pi/OpenCode Go `deepseek-v4-flash` (max). In Codex App, the Codex subAgent participant is dispatched natively through `multi_agent_v1` so the parent can see progress and reuse the same session. The OpenCode Go participant falls back first to Pi/DeepSeek V4 Flash max; the Codex participant fallback chain remains Kimi K3 high -> Pi/DeepSeek V4 Flash max -> CodeBuddy hy3 max. Chair fallback is Grok Build `grok-4.5`, then Cursor CLI `cursor-grok-4.5-high`.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Source Of Truth

- Current filesystem under this workbench is authoritative. Do not infer from
  deleted parent-session dialogue.
- Corrective contract and Codex acceptance:
  - `context/mw_ai_first_prefill_postconference_corrective_20260801_execution_context.md`
  - `plans/codex_execution_mw_ai_first_prefill_postconference_corrective_20260801.md`
  - `runs/execution/mw_ai_first_prefill_postconference_corrective_20260801/worker_01.md`
  - `runs/execution/mw_ai_first_prefill_postconference_corrective_20260801/worker_02.md`
  - `runs/execution/mw_ai_first_prefill_postconference_corrective_20260801/worker_03.md`
  - `runs/execution/mw_ai_first_prefill_postconference_corrective_20260801/manager.md`
  - `reviews/codex_execution_mw_ai_first_prefill_postconference_corrective_20260801_review.md`
  - `metrics/mw_ai_first_prefill_postconference_corrective_20260801_execution_metrics.md`
- Prior challenge and post-corrective runtime lineage:
  - `runs/conference/mw_ai_first_corpus_prefill_runtime_challenge_20260801/general_chair_pi_qwen38.md`
  - `context/mw_ai_first_corpus_prefill_runtime_20260801_context.md`
  - `runs/pi_mw_ai_first_corpus_prefill_runtime_20260801.md`
  - `reviews/codex_mw_ai_first_corpus_prefill_runtime_20260801_review.md`
  - `metrics/mw_ai_first_corpus_prefill_runtime_20260801_metrics.md`
- Authoritative implementation and focused tests:
  - `services/api/app/medical_writing_authoring_journey.py`
  - `services/api/app/medical_writing_authoring_prefill.py`
  - `services/api/app/medical_writing_authoring_prefill_ai.py`
  - `services/api/app/medical_writing_authoring_prefill_evidence.py`
  - `services/api/app/medical_writing_authoring_prefill_evidence_binding.py`
  - `services/api/app/medical_writing_authoring_prefill_corpus_bridge.py`
  - `services/api/app/ai_gateway.py`
  - `services/api/app/main.py`
  - `packages/contracts/workbench_contracts/models.py`
  - `tests/test_medical_writing_authoring_prefill*.py`
  - `tests/test_medical_writing_structured_design_contract.py`
  - `tests/test_medical_writing_authoring_journey.py`
- r6 is read-only acceptance evidence:
  `/private/tmp/mw-ai-first-prefill-corrective-r6-dXvRmZIn`.
  The original source runtime remains read-only at
  `/private/var/folders/yb/31r9763x6_54mdxswxk36c4w0000gn/T/mw-phase0b-browser-rwanbzol/runtime_glm_retest4`.

## Scope

- In scope:
  - independently test the reasoning and source evidence behind all ten prior
    challenge rechecks;
  - inspect the post-corrective adoption, catalog identity, reservation,
    recommendation, evidence-binding, semantic-gap, negation, and display
    contracts;
  - determine whether the r6 evidence proves one logical call, at most one
    physical POST, one event, zero adoption, isolated schema migration, and
    zero non-authoring logical deltas;
  - challenge the remaining user workflow, including an empty recommendation,
    frontend selection fallback, disabled card adoption, the audited
    user-edit channel, and the newly corrected open-label-extension preview;
  - classify every finding P0-P4 and return READY only if no P0-P4 remains.
- Out of scope:
  - product/source/runtime edits;
  - service start/stop, browser actions, model calls, OCR, translation,
    triage, download, preparation, adoption, Synopsis, CSR, DOCX release, and
    final multi-model launch testing;
  - medical-monitoring files or databases;
  - production promotion.

## Success Criteria

- Each selected primary route returns an auditable output or an explicit health/fallback reason.
- The prompt uses the correct Agent identity, provider/model, effort, tools-enabled policy, and same-session continuation policy.
- The runner records session, usage/tool observations, fallback decisions, and failure reasons without `--max-turns 1`.
- No production path is read or modified; Codex retains final acceptance.
- Every participant independently cites exact file/function/test/runtime
  evidence and identifies contradictions rather than accepting manager claims.
- The chair reconciles participant disagreements and gives one of:
  `READY_NO_P0_P4`, `NOT_READY`, or `EVIDENCE_BLOCKED`.
- `READY_NO_P0_P4` requires an explicit no-issue scope and residual risks that
  are outside this bounded slice; any P0-P4 finding must include the smallest
  concrete remediation and exact recheck.

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
- Read-only SQLite queries are allowed. Do not mutate r4/r5/r6, the source
  runtime, or product files.
- Existing tests may be inspected; rerun only the focused read-only test
  command if necessary to disprove a recorded claim. Do not start services or
  issue product AI calls.
- No OCR ran in this slice. Future new OCR uses official API
  `PaddleOCR-VL-1.6`; GLM-started files finish with GLM-OCR.

## Loop Log

- 2026-08-01 18:09:35: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-08-01 18:10 CST: source packet, scope, success criteria, P0-P4 gate,
  and read-only boundaries completed before dispatch.
