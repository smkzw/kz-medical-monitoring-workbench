# Task Context: mw_protocol_p0_phase0b_runtime_draft_word_20260801

Created: 2026-08-01 21:46:21
Objective: 在医学写作专用隔离 runtime 中验证 Phase 0B 阻塞章节的 AI 先起草、证据化可审阅内容、就绪状态与真实 Word 门，不重复任何冻结上游并保护医学监查边界
Task type: `html_ppt_visual_browser`
Risk: `high`
Selected agent route: `alibaba` / `qwen3.8-max-preview` / `xhigh`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `runs/MW_PROTOCOL_P0_PHASE0B_OFFLINE_READINESS_CHECKPOINT_20260801_1007.md`
- `context/mw_protocol_p0_phase0b_rebaseline_20260801_context.md`
- `reviews/codex_mw_protocol_p0_phase0b_rebaseline_20260801_review.md`
- `reviews/codex_conference_mw_protocol_p0_phase0b_readiness_challenge_20260801_review.md`
- Current workbench source under `services/api/app/`, `packages/contracts/`,
  `frontend/src/`, and focused tests, with current filesystem hashes treated
  as authoritative.
- Existing isolated evidence clones are read-only evidence only:
  `/private/tmp/mw-ai-first-prefill-corrective-r6-dXvRmZIn` and
  `/private/tmp/mw-ai-first-prefill-postchallenge2-r7-ZrfcXkYK`.
- The shared medical-monitoring runtime and task records are explicitly out of
  scope. No stable service is running at this checkpoint.

## Scope

- In scope: design the next bounded runtime slice that starts the current
  medical-writing API/frontend against a fresh task-scoped runtime root,
  exercises one real AI-first `AI 先起草` path on a typed actionable blocker,
  inspects the actual browser result, checks the document-level readiness
  projection, then performs the existing real DOCX/Word acceptance path if the
  draft reaches the export gate.
- In scope: read-only comparison of source/runtime identities, focused
  deterministic tests, task-scoped service logs, browser screenshots, DOCX
  artifacts, and concise durable evidence under this task's context/runs/
  reviews/metrics/logs surfaces.
- Out of scope: r42 or any frozen upstream replay; triage, candidate lock,
  download, preparation, OCR, translation, attempt 2/3, ready/excluded rows;
  Synopsis, CSR, final three-route release testing; any stable runtime or
  medical-monitoring source/test/database/WAL/SHM/task record; any product
  source edit in this planning pass.

## Success Criteria

- A fresh runtime root is created with online SQLite backup semantics and
  stable/monitoring fingerprints are either absent or proven unchanged; no
  shared runtime path is written.
- Current API/frontend starts only on task-scoped ports and returns matching
  runtime build identities without importing shared monitoring state into the
  stable runtime.
- One Computer Use browser action reaches an actionable typed blocker and
  invokes `AI 先起草` exactly once; the resulting proposal is evidence-bound,
  reviewable, and does not silently convert unknown/high-impact facts into
  project facts.
- Repeated refresh/restart or duplicate intent is idempotent; a later manual
  edit cannot be overwritten by a blank-draft proposal.
- The document-level readiness projection remains fail-closed until all
  applicable sections are substantive/structural or carry explicit actionable
  blockers; no ready/freeze/export claim is made from a partial draft.
- If the existing export path becomes eligible, the same task-scoped artifact
  is opened in real Microsoft Word, updated/saved/reopened, and visually
  checked. If it cannot become eligible, the exact blocking contract and next
  safe action are recorded instead.
- All claims distinguish offline-tested, real-runtime-verified, and Word-
  accepted evidence; no completion claim is made for the broader Protocol P0.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- This first delegated pass is plan-only. It may not start services, browser,
  Word, product AI, OCR, translation, or any external model call; Codex will
  separately authorize the actual runtime slice after reviewing the plan.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-01 21:46:21: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-01 21:47 CST: Re-anchored from the no-loss pause. Phase 0B offline
  readiness is accepted; runtime/browser/product-AI/Word gates remain open.
- 2026-08-01 22:05 CST: After a model change, Codex re-read the complete
  global `/Users/smkzw/.codex/AGENTS.md`, workspace and workbench `AGENTS.md`
  files (including `frontend/AGENTS.md`), the r42 no-loss checkpoint, the
  approved commercial-writing roadmap, and its independent challenge. The
  overall Goal remains active. The current safe boundary is unchanged:
  Protocol P0 remains first, Synopsis and CSR remain later; frozen r42
  upstream rows and the medical-monitoring lane are out of scope.
- 2026-08-01 22:05 CST: The delegated Qwen plan was reviewed as advisory. The
  next action is the explicitly bounded task-scoped runtime slice: online
  SQLite backups and fingerprints, task-only API/frontend ports, one real
  Computer Use `AI 先起草` action on a typed actionable blocker, readiness
  projection, and the evidence-ineligible export branch. No OCR, translation,
  upstream replay, or DOCX generation is authorized by this slice.

- 2026-08-01 22:18 CST: Runtime re-anchoring and closeout evidence completed.
  The task-scoped API/frontend ran on ports `18901/18902` with runtime root
  `runs/runtime_phase0b_20260801`; 21 SQLite databases passed
  `integrity_check=ok`. Source-clone SQLite hashes remained unchanged. Logical
  dumps matched source for 19/21 stores; the only expected clone-local deltas
  were `medical_writing_fact_intake.sqlite3` and
  `medical_writing_authoring_journey.sqlite3`.
- 2026-08-01 22:18 CST: Computer Use selected the target III-phase MG project
  and performed one bounded fact-intake submission. The independent AI route
  completed as `alibaba_token_plan / qwen3.8-max-preview`, persisted one
  `fact_intake_turn_completed` event, 20 reviewable proposals, and high-impact
  unknowns instead of inventing dose or schedule values. No duplicate fact
  event or durable job was created.
- 2026-08-01 22:18 CST: Local framing edits (technology/route/design/population)
  reached the real impact preview. The preview listed downstream invalidation
  (competitor search plan, corpus coverage, eligibility, intervention, goals,
  PICOS, synopsis, safety, SoA, flowchart and rationale). Codex used Computer
  Use to choose `返回修改`; the confirmation was not submitted. The formal
  journey therefore remains revision 8, `framing_complete=false`,
  `picos_complete=false`, corpus `not_ready`, and no greenfield document.
- 2026-08-01 22:18 CST: The AI-first full-document draft, document readiness,
  DOCX export and Microsoft Word acceptance were not reached. This is a
  deliberate fail-closed boundary, not a production-readiness claim. No
  triage, candidate lock, download, preparation, OCR, translation, retry,
  ready/excluded mutation, upstream research-pipeline start, or medical-
  monitoring operation occurred in this slice. Both task services were stopped
  and ports `18901/18902` are closed.
- 2026-08-01 22:18 CST: Evidence is under
  `runs/runtime_phase0b_20260801/evidence/`, including UI screenshots/AX
  snapshots, fact-intake response, journey state, durable-job inventory,
  post-stop process scope, source hashes, logical-dump comparison and
  integrity results. The no-loss continuation point is
  `runs/MW_PROTOCOL_P0_PHASE0B_RUNTIME_DRAFT_WORD_NO_LOSS_PAUSE_20260801_2218.md`.

## Current Safe Continuation

1. Audit or repair the UI contract that carries persisted fact-intake
   proposals into the formal framing/PICOS review surface; use Computer Use
   for any later adoption or commit. Do not substitute an API click.
2. Before any impact confirmation, prove that the clone-only commit cannot
   start or replay the frozen research pipeline. Keep r42 upstream rows and
   immutable identities untouched.
3. Only after a document exists and corpus/readiness gates are explicitly
   satisfied may the same clone attempt one real AI-first full draft, then
   document readiness and Word acceptance. The final three-route,
   two-role/multi-indication release matrix remains later and was not started.
