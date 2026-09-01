# Task Context: mw_ai_first_corpus_prefill_runtime_20260801

Created: 2026-08-01 13:27:05
Objective: 在全新隔离runtime中用真实独立AI和Computer Use验证来源绑定的Protocol证据能生成非空、受限、可审阅的设计候选且不改写旧revision
Task type: `html_ppt_visual_browser`
Risk: `high`
Selected agent route: `alibaba` / `qwen3.8-max-preview` / `xhigh`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Current workbench source after accepted finite-code slice
  `mw_ai_first_corpus_prefill_bridge_20260801`.
- Accepted code review:
  `reviews/codex_execution_mw_ai_first_corpus_prefill_bridge_20260801_review.md`.
- Existing evidence runtime
  `/private/var/folders/yb/31r9763x6_54mdxswxk36c4w0000gn/T/mw-phase0b-browser-rwanbzol/runtime_glm_retest4`
  is read-only source material for the new isolated clone.
- Existing journey `proj_user_cfd2d29284c8`, revision 6; old package
  `mwprefill_c9dda751f902c673a122` remains immutable evidence.
- Current filesystem and new isolated runtime database/browser state are the
  final truth.

## Scope

- In scope:
  - create a new temporary isolated runtime from an online-consistent,
    read-only backup of the current evidence runtime;
  - preserve provider settings and project evidence within that clone;
  - start current-code API and Vite on new localhost ports only;
  - use Computer Use for the one real `更新建议` action;
  - verify a new journey revision/package/AI run is appended, old revision 6
    and old package remain unchanged, and non-empty corpus-grounded candidates
    are limited to pending review;
  - inspect the actual UI and durable SQLite/audit lineage.
- Out of scope:
  - restart, stop, contact, or mutate the existing 18911/15174 runtime;
  - replay triage, preparation, OCR, translation, or medical review;
  - touch medical-monitoring source or authoritative data;
  - auto-adopt pending candidates, draft full Protocol, Synopsis, CSR, export,
    or final release-matrix testing in this slice.

## Success Criteria

1. New runtime starts from current source on distinct free ports and retains
   the exact project/analysis/source rows.
2. One Computer Use click creates exactly one new prefill request; no API
   substitution or duplicate click.
3. Generation catalog includes the 8 verified corpus entries and the AI
   returns at least one non-empty review candidate derived from them.
4. Every single-source corpus candidate is
   `pending_decision / competitor_option / partially_supported`, carries
   source locator/hash and visible limitation; no exact fact is silently
   promoted.
5. Old journey revision 6, old package, corpus analysis, source spans,
   preparation/translation/admission rows and existing runtime main DB hashes
   remain unchanged.
6. Actual browser rendering is coherent and the user burden is materially
   lower than the prior 13-field blank form; any remaining gaps are explicit.

## Risk Boundaries

- Writes are allowed only inside a newly created temporary runtime directory,
  this task's context/runs/reviews/metrics, and runtime process logs.
- Copy SQLite stores with online backup semantics; do not copy live WAL/SHM as
  the logical snapshot mechanism.
- Do not expose credentials in logs. Copy provider credential files locally
  without printing their contents.
- Stop on source-identity/hash failure, any write to the existing runtime,
  duplicate model call, exact-fact promotion, or inability to distinguish the
  new package/revision from old immutable evidence.
- The delegated route is reserved for later independent review if needed.
  Codex performs Computer Use actions and final runtime/browser acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-01 13:27:05: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-01 13:36-14:13 CST: four clean-clone runtime attempts were used
  serially. Each clone started from the same revision-6 online SQLite backup;
  each received exactly one Computer Use `更新建议` action and was never reused
  for a second model request.
  - r1 proved that the 200-entry model projection starved all eight round-1
    Protocol findings behind ClinicalTrials.gov registry entries.
  - r2 proved the stable priority projection exposed all eight findings, but
    the first accepted corpus candidate did not visibly surface its
    insufficient-support limitations.
  - r3 proved the provider can nondeterministically ignore all eight corpus
    findings even when they are present in the model input.
  - r4 added a deterministic, server-side review-only extraction fallback
    after a successful real provider call. It extracts only controlled design
    terms explicitly present in a verified, sent, single-source Protocol
    quote and routes the result through the same strict binding validator.
- Code contract after correction:
  - current-project facts remain first priority; verified round-1 findings are
    second; registry entries fill the remaining projection budget;
  - `insufficient_support_do_not_generalize` findings are always
    `pending_decision / competitor_option / partially_supported /
    manual_only`;
  - visible gaps include “不得视为当前项目事实”, the source limitation, and
    unresolved provenance gaps;
  - the deterministic fallback may populate only explicitly matched
    randomization, blinding, assignment, center, placebo-control, or
    open-label-extension terms; all other values stay empty;
  - exact/current-project facts are not inferred or overwritten.
- Verification after the final code:
  - focused authoring/prefill suite: 480 passed, 17 pre-existing deprecation
    warnings;
  - Python compilation passed for the changed AI, binding, and bridge modules;
  - changed-file SHA-256:
    - `medical_writing_authoring_prefill_ai.py`
      `2e03a8f91c802e6fb4e05110c1b99ca34f91589a57f0a3782445f291c1400ee2`;
    - `medical_writing_authoring_prefill_evidence_binding.py`
      `1f216fc3feba32bb99f7628fc8e0fe80050f53b904ea2469f540c466f8456f4b`;
    - `test_medical_writing_authoring_prefill_corpus_bridge.py`
      `c331e9d7ee30ba5ef724c1695063f299be55dbcc84234efff3caae2e05fb1351`.
- 2026-08-01 14:13 CST: final clean clone
  `/tmp/mw-ai-first-prefill-runtime-r4-1eQtHYQD` passed 18 SQLite
  `quick_check`s and started on API 18915 / Vite 15178. One real Computer Use
  click produced revision 7 and exactly one new event:
  `mwjourney_event_986324805143565fd3a244b2`,
  `authoring_journey_prefill_generated`, AI run
  `mwprefillrun_cb543a82aeeea2a345af5ce7`,
  provider/model `alibaba_token_plan / qwen3.8-max-preview`.
- Final persisted/browser candidate:
  - field `package.design`, candidate
    `mwprefilleb_f8df40e0ef4ac2cd`;
  - preview `竞品Protocol观察：开放标签、随机、平行分组`;
  - only `design.blinding=开放标签`,
    `design.randomization=随机`, and
    `design.assignment_model=平行分组` are non-empty;
  - three claim bindings resolve to the same verified NCT04735432 Protocol
    quote; seven visible evidence gaps include the not-current-project warning
    and single-source/source-purpose limitations;
  - ten other design decisions remain blank; the candidate is pending,
    manual-only, and the adoption button remains disabled until review.
- Logical delta audit:
  - source target remains revision 6/state
    `959f7c1303aacd52b0b73a6e4062541e757fd1790681a02bc5e97aa74ac90c49`;
  - clone target is revision 7/state
    `aaf844a19e1821580b822e2719f5a81fc281f1ee7de1b5d6304d7c679deb0b7f`;
  - all non-target journeys are byte-logically identical;
  - source events are a strict subset of clone events and the only clone-only
    row is the generation event above;
  - adoption-event counts are unchanged at 1/1; no candidate was adopted;
  - schema migrations are identical;
  - `.dump` SHA-256 values are identical source versus clone for
    `writing_reference`, durable jobs, shared corpus, fact intake, greenfield,
    literature, assembly plan, synopsis import, and user projects. This proves
    no preparation, OCR, translation, triage, corpus, or project row changed.
- OCR route correction retained for all subsequent testing:
  use official API `PaddleOCR-VL-1.6` for files not yet started; any file that
  already started with GLM OCR remains GLM through terminal completion. This
  runtime slice made zero OCR calls.

## Current Decision

`RUNTIME_CORE_READY / INDEPENDENT_CONTRADICTION_REVIEW_PENDING`

The AI-first Protocol evidence bridge now has deterministic real-runtime proof
without promoting competitor observations into project facts. A read-only
independent challenge must still inspect the final code, tests, clone lineage,
and rendered evidence before this slice is accepted into the continuing
Protocol P0 route. No phase pause is requested.

## Post-Conference Corrective And r6 Addendum

- The prior independent challenge returned `NOT READY` with bounded P2-P4
  findings. Execution task
  `mw_ai_first_prefill_postconference_corrective_20260801` corrected the
  adoption gates, next-revision evidence identity, exactly-once reservation,
  unsupported-term gaps, safe recommendation, wording, evidence-ref
  deduplication, negation, and prompt newline contracts.
- Manager and Codex each observed 601 focused tests passing with 17 baseline
  warnings.
- r5 real runtime proved one residual P4 preview defect:
  `竞品Protocol观察：开放标签、是`. It was a display projection defect only.
- The source now maps that preview value to `开放标签延展` while preserving
  structured `design.open_label_extension="是"` and all bindings.
- r6 source-derived clone
  `/private/tmp/mw-ai-first-prefill-corrective-r6-dXvRmZIn` passed 21 SQLite
  quick checks and one real Computer Use generation on 18917/15180:
  - source revision 6/schema v1 remains untouched;
  - r6 revision 7/schema v2, state
    `48a4bc72323abd077bd9e1133f188f6456ecf22121d00b1e6d6213c04233a106`;
  - one logical call `mwprefillcall_823b9a7cb84940de8c9a44c9`;
  - one transport attempt, one completed event, zero adoption;
  - real UI renders
    `竞品Protocol观察：开放标签、开放标签延展`;
  - nine non-authoring writing stores remain logically identical.
- Current decision:
  `POST_CORRECTIVE_RUNTIME_READY / NEW_INDEPENDENT_CHALLENGE_PENDING`.

## Second Challenge Corrective Acceptance And No-Loss Pause

- The new independent challenge returned bounded P2-P4 findings. Execution
  `mw_ai_first_prefill_postchallenge2_corrective_20260801` corrected:
  composite per-path policy bypass, empty-slot unsafe fallback, dead
  single-card actions, policy/conflict error mapping, draft catalog
  diagnosis, reservation owner/race telemetry, force/replay explanations,
  manual-only recommendation, and controlled-term negation.
- Serial route:
  DeepSeek V4 Flash workers `019fbcfd…`, `019fbd19…`, `019fbd51…`; Cursor
  manager `f9676c8a…`; no fallback.
- Manager: 727 authoring-focused tests passed.
- Codex: 748 expanded focused tests passed with 17 baseline warnings; Node QC
  passed.
- r7 acceptance clone
  `/private/tmp/mw-ai-first-prefill-postchallenge2-r7-ZrfcXkYK` was made by
  online backup from r6. Computer Use on 18918/15181 made only client-side
  selections:
  - empty recommended slot stayed empty;
  - unsafe recommendation/adoption buttons were disabled with reasons;
  - selecting a restricted design exposed 13 explicit confirm-or-skip paths
    and kept adoption disabled;
  - single-field deterministic-failure adoption actions were absent.
- The r7 API log contains GET only. There was no new generation, adoption,
  provider transport, OCR, translation, triage, download, or source-runtime
  write.
- r7 and r6 have identical `.dump` SHA-256 for 21/21 SQLite stores. The
  project remains revision 7/state `48a4bc…`; reservation remains completed
  with one transport and the original logical-call/event identity.
- All temporary r4-r7 services were stopped; ports
  18915/15178 through 18918/15181 are closed. Clones and evidence remain.
- Current decision:
  `POSTCHALLENGE2_CORRECTIVE_ACCEPTED / USER_REQUESTED_NO_LOSS_PAUSE`.
- Exact next action after an explicit continue request: re-anchor from the
  current filesystem and
  `runs/MW_AI_FIRST_PREFILL_POSTCHALLENGE2_NO_LOSS_PAUSE_20260801_2124.md`;
  do not repeat completed generation, triage, OCR, translation, conference,
  or corrective execution.
