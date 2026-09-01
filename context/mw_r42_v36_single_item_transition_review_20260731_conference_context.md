# Conference Context: mw_r42_v36_single_item_transition_review_20260731

Created: 2026-07-31 23:37:11
Objective: Independently challenge the implemented single-item v36 downstream-contract transition for r42: prove source immutability, exact target scope, current-contract identities, abbreviation fail-closed behavior, and duplicate/restart model-call safety; return READY only if no P0-P4 defect remains
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

- Current filesystem under this workbench.
- `runs/MW_R42_NO_LOSS_PAUSE_20260731_1609.md` (boundary only; do not
  inspect either runtime directory it names).
- `plans/mw_r42_v36_single_item_transition_20260731.md`.
- `context/mw_r42_v36_single_item_transition_20260731_context.md`.
- Changed implementation:
  - `packages/contracts/workbench_contracts/models.py`
  - `services/api/app/writing_reference_translation_batch.py`
  - `services/api/app/main.py`
  - `tests/test_writing_reference_translation_batch.py`
- Connected, preserved implementation/evidence:
  - `services/api/app/writing_reference_repository.py`
  - `services/api/app/writing_reference.py`
  - `services/api/app/chapter_translation_pipeline.py`
  - `tests/test_writing_reference_translation_durable_jobs.py`
  - `tests/test_mw_v11_translation_alignment.py`
- Current verified commands:
  - `python3 -m unittest -q tests.test_writing_reference_translation_batch`
    -> 50 passed before the final OpenAPI-only test was added; the four new
    transition tests separately pass.
  - `python3 -m unittest -q tests.test_writing_reference_translation_durable_jobs`
    -> 33 passed.
  - `python3 -m unittest -q tests.test_mw_v11_translation_alignment`
    -> 170 passed.
- Intake hashes for preserved connected files are recorded in
  `context/mw_r42_v36_single_item_transition_20260731_context.md`.

## Scope

- In scope:
  - Read-only independent audit of the four changed files and connected
    persistence/pipeline/test contracts.
  - Challenge whether the ordinary retry was correctly rejected for the
    fidelity-blocked source and whether the new API can target only one source
    item.
  - Check immutable source preservation, new plan/chunk/integration/candidate
    identity, semantic and request idempotency, exact durable payload/claim,
    duplicate-worker behavior, and crash windows before/after external calls.
  - Check that `VISIT`/`SCHEDULE` false positives pass while an omitted `ECG`
    remains blocked.
  - Return delta-only P0-P4 findings with file/line locators, failed path,
    remedy, and recheck; READY requires no unresolved P0-P4 finding.
- Out of scope:
  - Editing any source, test, task record, or runner-owned report.
  - Starting services, opening ports, contacting models/oMLX, or running OCR,
    translation, downloads, clone runtime, or original r42 runtime.
  - Reading either
    `runs/execution/mw_final_5x3_harness_20260728/rounds/release-r42-20260730/slots/A1/lazy_medical_writer/runtime`
    or `runs/execution/mw_r42_planner_retry_20260731/runtime`.
  - Re-running triage, preparation, OCR, old attempts, ready/excluded items,
    Synopsis, CSR, browser release, or medical-monitoring work.

## Success Criteria

- Each selected primary route returns an auditable output or an explicit health/fallback reason.
- The prompt uses the correct Agent identity, provider/model, effort, tools-enabled policy, and same-session continuation policy.
- The runner records session, usage/tool observations, fallback decisions, and failure reasons without `--max-turns 1`.
- No runtime path is read or modified; Codex retains final acceptance.
- Review explicitly tests the strongest contradiction to exactly-once model
  behavior: process death after dispatch, after immutable output persistence,
  and before terminal item projection.
- Review distinguishes logical bounded correction from an accidental repeated
  invocation after duplicate request/worker/restart.
- Review checks API and startup durable-job routing, not only the service
  helper in isolation.

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
- Do not trust comments or tests alone; trace the database constraints, CAS,
  durable payload, executor branch, output recovery, and immutable IDs.
- Existing unrelated work is user-owned and must remain untouched.

## Loop Log

- 2026-07-31 23:37:11: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-07-31 23:39 CST: Source/scope packet completed. This conference is
  read-only and cannot inspect or execute either runtime.
- 2026-07-31 23:40:48 CST: Participant routes launched once in parallel.
  The native Codex child handle is `/root/r42_v36_codex_challenge`; the
  Pi/DeepSeek runner PTY session is `29704`. No fallback, redispatch, or
  controller polling has occurred.
- 2026-07-31 23:52 CST: Both first passes completed in their original
  sessions. The native participant reproduced a P1 lease-takeover race:
  stale stage persistence returned silently and allowed two external calls.
  Pi/DeepSeek reported additional P3/P4 recovery-contract gaps. Verdict:
  `NOT READY`.
- 2026-07-31 23:58 CST: Codex repaired the P1 root cause and the actionable
  P4 gaps. Stage persistence now raises ownership loss on a stale/missing CAS
  and rechecks ownership after committed call intent; ordinary retry rejects
  transition child batches; restart-before-intent has a distinct error code;
  the route declares an explicit response model. New two-owner and crash
  interleaving tests plus all connected suites passed: `258 tests`.
- 2026-07-31 23:59:50 CST: Delta-only re-review was sent to the same native
  child handle and resumed in the same Pi session
  `019fb8d5-ba6e-7000-9a06-070d081bff31`; Pi runner PTY session is `46596`.
  No fallback or new participant session was created.
- 2026-08-01 00:08 CST: Both same-session rechecks returned `READY` with no
  unresolved P0-P4 finding. Pi retained session
  `019fb8d5-ba6e-7000-9a06-070d081bff31`; native child retained
  `/root/r42_v36_codex_challenge`.
- 2026-08-01 00:09:24 CST: Guard-selected sub-venue chair
  Pi/Alibaba `qwen3.8-max-preview` was launched once after both participant
  rechecks completed. Runner PTY session is `86589`; no fallback is active.
- 2026-08-01 00:20 CST: Chair completed in session
  `019fb8f0-0477-7000-b300-dc95f8a2e711`, independently reran `258` tests,
  and returned `READY`. No fallback was activated. Codex final hash and port
  checks agreed; conference closed with zero unresolved P0-P4 findings.
