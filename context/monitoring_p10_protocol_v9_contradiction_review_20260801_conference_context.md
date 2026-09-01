# Conference Context: monitoring_p10_protocol_v9_contradiction_review_20260801

Created: 2026-08-01 10:06:31
Objective: Independent read-only contradiction review of the offline monitoring protocol v9 postpositive modal-role and visible-scope corrective before any runtime canary
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

- Current filesystem.
- `context/monitoring_p10_protocol_v9_visible_scope_postpositive_corrective_20260801_context.md`
- `runs/pi_monitoring_p10_protocol_v9_visible_scope_postpositive_corrective_20260801.md`
- `runs/pi_monitoring_p10_protocol_v9_visible_scope_postpositive_corrective_20260801_followup1.md`
- `services/api/app/monitoring_ai_service.py`
- `services/api/app/monitoring_protocol_preparation_service.py`
- `tests/test_monitoring_ai_service.py`
- `tests/test_monitoring_protocol_preparation.py`
- `tests/test_monitoring_ai_api.py`
- Current accepted hashes:
  - `monitoring_ai_service.py`: `4d97114e1bb9a4530954bdd0282abb106cc4dc08b07c40dc3c87eafeaf1f24ee`
  - `monitoring_protocol_preparation_service.py`: `08207529f0a17156c55843e2003d2c2746c9721154312dacd5783b0a7e2081ef`
  - `test_monitoring_ai_service.py`: `a907883c17a6bb61b96a83bb4a22277bcc155b962cd19dbb79c3758915a57ed3`
  - `test_monitoring_protocol_preparation.py`: `dd26a2ff10089d06f3053843fd135cb970160a26d19f69ef9a35b056877aa6f6`
  - `test_monitoring_ai_api.py`: `3704acd94839a6f7d0136c4e0d30cc1594a9ce5bf16e380e849cb3a9a71a44f0`
- Codex verification:
  - two implementation modules compile;
  - three focused files: `403 passed`;
  - six-phrase withheld semantic-role matrix: all exact results pass;
  - monitoring selection with the known unrelated collection blocker ignored:
    `1398 passed, 4285 deselected`;
  - five adjacent medical-writing contract files: `200 passed`.
- Standard `pytest -q tests -k monitoring` remains collection-blocked by
  `tests/test_medical_writing_dynamic_section_matrix.py` importing removed
  private `_REQUIRED_CORE_BODY_SEMANTIC_IDS`; this is parallel medical-writing
  drift and out of scope.

## Scope

- In scope: independent read-only contradiction review of prompt v9 identity and
  visible-field exclusion wording, v8 terminal cutover, postpositive
  reschedule/schedule semantic-role correction, exact fail-closed guardrails,
  and whether the offline slice is safe to pause before a future fresh canary.
- Out of scope: edits, services, ports 8911/5174, provider calls, runtime DBs,
  RUX/MY009 or any real project, candidate decisions, medical-writing repair,
  broad negation exemptions, or final release/canary acceptance.

## Success Criteria

- The existing native Luna reviewer returns an auditable delta-only review;
  no new reviewer session is created.
- Findings distinguish blocking defects from residual conservative behavior and
  the unrelated medical-writing collection blocker.
- Review explicitly challenges modal/predicate positional pairing, numeric and
  quantified guardrails, negative-scope disclaimer behavior, v8-to-v9 cutover,
  and absence of runtime writes.
- No file is modified by the reviewer; Codex remains final authority.

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

## Loop Log

- 2026-08-01 10:06:31: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-08-01: Pi initial pass and one same-session follow-up completed without
  fallback. Codex focused and broad offline regressions passed as recorded
  above. Ports 8911/5174 remained stopped and v9 runtime counts remained zero.
- This conference reuses native reviewer `/root/rux_protocol_v4_audit`; it does
  not create a new Codex subAgent. The prior Pi implementation pass and Codex
  main-venue verification supply the complementary implementation and chair
  perspectives, so no duplicate artifact-production role is dispatched.
