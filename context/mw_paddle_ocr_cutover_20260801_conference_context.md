# Conference Context: mw_paddle_ocr_cutover_20260801

Created: 2026-08-01 11:34:48
Objective: 只读反证审阅医学写作 PaddleOCR-VL-1.6 文件级切换、429退避并发与回退审计合同
Task type: `high_risk_contradiction_review`
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

- Current filesystem under this isolated workbench is authoritative.
- Read set:
  - `services/api/app/main.py`
  - `services/api/app/paddle_ocr_adapter.py`
  - `services/api/app/ocr_fallback_orchestrator.py`
  - `services/api/app/writing_reference.py`
  - `services/api/app/writing_reference_preparation_batch.py`
  - `services/api/app/writing_reference_ocr_evidence.py`
  - `packages/contracts/workbench_contracts/models.py`
  - `tests/test_writing_reference_preparation_batch.py`
  - `tests/test_omlx_role_gate_integration.py`
  - `tests/test_paddle_ocr_primary_fallback.py`
  - `tests/test_ai_role_runtime_settings.py`
- Runtime evidence supplied by Codex:
  - real 200-DPI Paddle probe passed in 2.786 seconds;
  - first post-cutover document persisted 28 Paddle pages and 3 correctly
    attributed GLM fallbacks after Paddle submit HTTP 429;
  - mixed-model QC triggered once with verdict `review_required`;
  - 106 focused tests and compileall passed after the bounded remediation.
- Official primary sources:
  - `https://github.com/PaddlePaddle/PaddleOCR`
  - `https://github.com/PaddlePaddle/PaddleOCR/blob/main/docs/version3.x/pipeline_usage/PaddleOCR-VL.en.md`

## Scope

- In scope: read-only contradiction review of document-pinned OCR model
  resolution, Paddle official async submit/poll parsing, hosted-provider
  concurrency cap, bounded 429-only submit retry with non-idempotent 5xx
  fail-closed, GLM fallback provenance,
  mixed-model QC trigger, fail-closed behavior, and focused test coverage.
- Out of scope: edits, service startup/restart, live credential access,
  network calls, full-app import, test execution, completed OCR replay,
  translation, Protocol authoring, Synopsis, CSR, monitoring files, and r42
  immutable data.

## Success Criteria

- Each selected primary route returns an auditable output or an explicit health/fallback reason.
- Findings are delta-only P0-P4 with exact file/line evidence and distinguish
  observed facts from inference.
- No retry path can silently duplicate a successful Paddle job, mislabel GLM
  output as Paddle, or let a live role change invalidate an in-progress
  document's pinned model.
- Retry/concurrency behavior is bounded, auditable, credential-safe, and
  covered by deterministic tests; remaining gaps are explicit.
- The prompt uses the correct Agent identity, provider/model, effort, tools-enabled policy, and same-session continuation policy.
- The runner records session, usage/tool observations, fallback decisions, and failure reasons without `--max-turns 1`.
- No source/runtime file is modified and no full application is imported;
  Codex retains final acceptance.

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
- The active attempt-1 21-document runtime must not be restarted, retried, or
  mutated by reviewers.
- Allowed outputs are runner-owned conference reports only; participants
  return text and do not write report files themselves.

## Loop Log

- 2026-08-01 11:34:48: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-08-01 11:36 CST: Codex completed the source, scope, success, risk, and
  write-boundary contract; native Codex participant already dispatched once.
- 2026-08-01 11:49 CST: participant challenge identified durable pin,
  accepted-job ambiguity, restart, and concurrency gaps. Codex remediated
  those gaps without restarting the active runtime.
- 2026-08-01 11:56 CST: retry is now 429-only with a 30-second delay cap;
  submit 5xx/URLError and all post-acceptance ambiguity fail closed. Paddle
  outcome-unknown items are excluded by both retry selection and worker claim.
- 2026-08-01 11:58 CST: 105 focused tests and compileall passed; native
  Codex participant completed same-session delta review with READY.
- 2026-08-01 12:11 CST: Pi/DeepSeek same-session round 2 completed READY and
  identified one retry-boundary P3: a non-integer JSONL page index escaped
  Paddle outcome-unknown classification. Codex made the bounded correction,
  added job-id-preserving coverage, replaced the restart model literal with
  the shared Paddle model constant, and re-ran the four focused suites:
  106 passed with 17 baseline deprecation warnings; compileall passed.
