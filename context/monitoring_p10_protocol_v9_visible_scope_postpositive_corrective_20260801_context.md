# Task Context: monitoring_p10_protocol_v9_visible_scope_postpositive_corrective_20260801

Created: 2026-08-01 09:31:37
Objective: Implement an offline fresh v9 protocol prompt/validator corrective for the v8 RUX visit canary: forbid excluded topic/family repetition in all user-visible candidate fields and narrowly classify postpositive reschedule triggers without weakening full-boundary or exactly-one-family gates; add complete positive/negative tests and do not start services or write runtime data.
Task type: `finite_code_task`
Risk: `high`
Selected agent route: `deepseek` / `deepseek-v4-flash` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Current filesystem.
- v8 canary pause:
  `context/monitoring_p10_loop316_protocol_v8_visit_canary_pause_20260801.md`.
- v8 terminal evidence:
  `runs/monitoring_p10_loop316_protocol_v8_visit_canary_terminal_evidence_20260801.md`.
- Independent v8 review:
  `runs/codex-subagent_monitoring_p10_loop316_protocol_v8_visit_canary_20260801.md`.
- Codex v8 review:
  `reviews/codex_monitoring_p10_loop316_protocol_v8_visit_canary_20260801_review.md`.
- Governed implementation/tests:
  - `services/api/app/monitoring_ai_service.py`
  - `services/api/app/monitoring_protocol_preparation_service.py`
  - `tests/test_monitoring_ai_service.py`
  - `tests/test_monitoring_protocol_preparation.py`
  - `tests/test_monitoring_ai_api.py`
- Frozen pre-edit SHA-256 values:
  - `monitoring_ai_service.py`:
    `0485440a2af4c75bb243c0de36f6d5603bd39dfbdffb77dcf2a813c2bd81057d`
  - `monitoring_protocol_preparation_service.py`:
    `0231e1386cc7c37fd1f5f0eed4c226d6bc43f98bf1a0dbdb4da105c0d7624830`
  - `test_monitoring_ai_service.py`:
    `39bd0a580d4cd22c97a88f8e3b05035b9b836ef4b80b25642cd3bfafed816398`
  - `test_monitoring_protocol_preparation.py`:
    `df0bc517d66ca90d4fa74da46f43e77bec0c655ef70472fa1b096d39bc016bf1`
  - `test_monitoring_ai_api.py`:
    `81dfad4abb39e80ccfe65ee242dc78ba65fe88a365dd9cae73fc22ed1ae28c8e`

External-discovery decision: no web or package scan. This is a bounded
deterministic prompt/grammar correction with no dependency, architecture or
tool-adoption choice; the decisive evidence is the immutable v8 response and
local validator contract.

## Scope

- Writable paths are limited to the five governed files above.
- Required implementation:
  1. Move protocol-clause structuring to fresh prompt identity
     `monitoring-protocol-clause-structuring-v9`.
  2. Add v8 to the explicit terminal legacy set. Terminal v3-v8 history remains
     visible/auditable; queued/active legacy work remains fail-closed and fresh
     work receives v9 identity.
  3. In both initial and single-repair provider-visible visit contracts, forbid
     naming an excluded topic/action family in any user-visible field merely to
     say it is excluded, omitted or not structured. This applies to title, text,
     every structured string, claim text, uncertainty and user action. Guidance
     must be generic and topic-internal. The repair must remove offending phrases,
     not add negative scope disclaimers.
  4. Narrowly classify a postpositive reschedule trigger such as
     `计划访视无法在窗口内完成时的改期/补访安排` as reschedule-only. A schedule
     term followed by a trigger marker is non-independent only when the candidate
     has a real reschedule/unscheduled action and no independent normative,
     quantified, numeric-window, week/day or ordering assertion.
  5. Add exact positive/negative tests derived from the v8 output.
- Out of scope:
  - broad negation exceptions;
  - removing uncertainty/user action from the full boundary view;
  - global reschedule precedence;
  - weakening medication, dispensing/PK, withdrawal, safety, collection or
    exactly-one-family gates;
  - changing evidence packet, structural repair, claim anchors, error order,
    one-repair limit or whole-response atomicity;
  - modifying medical-writing, frontend, runtime databases, services, providers,
    browsers, projects or candidates.

## Success Criteria

- Prompt identity and repair suffix are v9; v8 joins terminal legacy history and
  is never reused for fresh work.
- Initial and repair contracts both explicitly cover every user-visible field and
  forbid exclusion-word repetition/negative scope disclaimers.
- A compliant rewrite of v8 repaired candidates 1-4 can satisfy the existing
  executable gates, while the exact original negative-disclaimer/off-topic
  surfaces remain fail-closed.
- Exact postpositive title
  `计划访视无法在窗口内完成时的改期/补访安排` is family
  `["reschedule"]`.
- Positive variants with trigger and action across punctuation/fields remain
  reschedule-only.
- Without a reschedule/unscheduled action, the same schedule wording remains
  schedule.
- Independent schedule obligations, quantified rules, numeric definitions,
  week/day timing, ordering, true mixed-family clauses and real negated
  prohibitions remain fail-closed as applicable.
- Existing complete candidate-indexed diagnostic order, single repair and zero
  partial persistence tests continue to pass.
- Worker compiles only the governed implementation files and runs only the three
  focused test files. Codex owns broader regressions and final acceptance.

## Risk Boundaries

- Do not start 8911/5174, call a provider/API, read or write runtime DBs, run RUX
  or MY009, or make any candidate/draft/activation decision.
- Do not touch current parallel medical-writing work. Its private-symbol drift is
  known but outside this slice.
- Do not accept provider prose or remove strict gates to make the canary pass.
- Preserve unrelated changes and stop if any governed pre-edit hash differs before
  editing.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Launch the declared Pi/deepseek route once and wait through the runner hard wait
  up to 120 minutes. Do not fixed-poll, duplicate dispatch or switch routes for
  latency.
- After completion Codex may send one consolidated same-session corrective only
  for actionable acceptance gaps. Fallback is allowed only after terminal route
  failure or exhausted recovery with failed acceptance.

## Loop Log

- 2026-08-01 09:31:37: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- Latest global/project AGENTS and `multi-agent-verification-loop` were read in
  full. Their hashes are `28029e...cd79`, `31d8b1...b001` and
  `40feb6...43a4`.
- Read-only freeze: 8911/5174 and task workers/tests are stopped; v4-v8 counts
  remain `8/8/8`, `1/1/0`, `1/1/0`, `1/1/0`, `1/1/0`; v9 is empty.
- All five governed hashes match the v8 pause anchor.
- Parallel medical-writing source changed again at 09:30 CST and the old test
  still imports a removed private symbol. This slice treats both writing files as
  read-only and will not repair or revert them.
- 2026-08-01 09:32-09:46 CST: Pi/deepseek session
  `019fbaf4-a806-7000-95e6-a3e88e33e3e3` completed the v9 implementation in
  one pass. Codex review reproduced a modal-role false positive in
  `…完成时必须改期/应重新安排`; one consolidated same-session follow-up
  corrected it. No fallback or duplicate dispatch was used.
- Final governed hashes:
  - `monitoring_ai_service.py`:
    `4d97114e1bb9a4530954bdd0282abb106cc4dc08b07c40dc3c87eafeaf1f24ee`
  - `monitoring_protocol_preparation_service.py`:
    `08207529f0a17156c55843e2003d2c2746c9721154312dacd5783b0a7e2081ef`
  - `test_monitoring_ai_service.py`:
    `a907883c17a6bb61b96a83bb4a22277bcc155b962cd19dbb79c3758915a57ed3`
  - `test_monitoring_protocol_preparation.py`:
    `dd26a2ff10089d06f3053843fd135cb970160a26d19f69ef9a35b056877aa6f6`
  - `test_monitoring_ai_api.py`:
    `3704acd94839a6f7d0136c4e0d30cc1594a9ce5bf16e380e849cb3a9a71a44f0`
- Codex verification: two modules compiled; three governed files
  `403 passed`; withheld six-phrase role matrix passed; standard full
  monitoring selector remained collection-blocked by the unrelated
  medical-writing private-symbol import; with that single file ignored,
  `1398 passed, 4285 deselected`; five adjacent medical-writing contract files
  `200 passed`.
- Reused native Luna reviewer `/root/rux_protocol_v4_audit`; no new reviewer or
  fallback. Independent result: no P0/P1 blocker; one P2 test-coverage gap for
  direct failed/RUNNING/same-revision queued v8 cutover behavior. The gap is
  recorded as a mandatory pre-canary offline check and does not block this
  offline pause.
- 2026-08-01 10:15 CST final process check: ports 8911 and 5174 have no
  listeners; no v9 runner or monitoring pytest remains. A separate process on
  port 18911 belongs to another workspace task and was not touched.
