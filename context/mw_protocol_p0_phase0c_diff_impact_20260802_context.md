# Task Context: mw_protocol_p0_phase0c_diff_impact_20260802

Created: 2026-08-02 00:56:03
Objective: 继续 Protocol P0 Phase 0C：为已持久化 selected_hash 的局部 AI 精改补齐确定性局部 diff 与最小下游影响投影；只在现有 RevisionThread/working-copy 合同内做可回滚、可审计增量，不触碰冻结 r42/v36、上游研究/OCR/翻译或医学监查并发线
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Immutable no-loss boundary: `runs/MW_R42_NO_LOSS_PAUSE_20260731_1609.md`.
- Approved Protocol-first roadmap and Phase 0C exit gates:
  `plans/mw_commercial_writing_gap_and_roadmap_20260731.md`.
- Product gap context and independent challenge:
  `context/mw_commercial_writing_gap_20260731_context.md` and
  `reviews/mw_commercial_writing_gap_20260731_independent_challenge.md`.
- Accepted prerequisite selected-hash slice:
  `runs/codex_mw_protocol_p0_phase0c_selected_hash_20260802.md`, plus its
  context/review/metrics records.
- Current authoritative code and deterministic tests under
  `packages/contracts/`, `services/api/app/`, `frontend/src/`, and `tests/`.
- Current filesystem is final truth. No runtime service, browser, external
  model, OCR/translation, download, upstream state, or medical-monitoring
  file is an authority or an allowed input for this bounded task.

## Scope

- In scope:
  - Read-only audit of the current RevisionThread/RevisionSuggestion,
    working-copy snapshots and existing `diff_patch`/accept/reject/rewrite
    paths.
  - Define one deterministic local diff contract derived from the immutable
    pre-apply selected text and proposal text, with stable ordering and no
    silent normalization that changes medical content.
  - Define the smallest evidence-backed downstream-impact projection already
    representable by current source/evidence/section identities; unknown or
    unbound dependents must fail closed or be explicitly marked unresolved.
  - If the audit proves a narrow gap, implement only the smallest additive,
    backward-compatible model/service/repository change and focused tests.
- Out of scope:
  - r42/v36 transition/retry, preparation, downloads, OCR, translation,
    attempts, ready/excluded items, or immutable upstream rows.
  - Synopsis, CSR, full semantic graph migration, DOCX/Word rendering,
    provider/model calls, production databases/services, browser automation,
    or the medical-monitoring concurrent lane.
  - Replacing existing revision application semantics or inventing a broad
    claim graph without authoritative local evidence.

## Success Criteria

- The current path and its gaps are evidenced with exact source/test locators.
- A diff result is deterministic for identical selected/proposed text, carries
  the selected hash/revision lineage, and is safe for legacy records.
- Impact output never claims a dependent is affected without an exact local
  identity; unresolved/unsupported propagation is visible and fail-closed.
- Focused deterministic tests and compile checks pass; no frozen checkpoint,
  runtime state, process, or monitoring file changes.
- The task remains a bounded Phase 0C increment and does not imply Protocol
  release readiness.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-02 00:56:03: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-02: The prerequisite selected-hash slice reached independent READY;
  this task is its separately tracked next safe action. The selected-hash
  source hashes and frozen r42 fingerprint remain recorded in its run file.
- 2026-08-02: Read-only reconnaissance began; no runtime service, model,
  browser, OCR/translation, download, or upstream/monitoring state was
  touched.
- 2026-08-02: Audit found `RevisionSuggestion.diff_patch` was only an
  AI-provided display string and the existing StudyDefinition impact service
  does not prove local text-range propagation. Implemented typed deterministic
  diff segments, proposal/source hash binding, and a read-only impact
  projection driven solely by exact `source_fact_ids`; missing edges and
  external evidence remain explicit unresolved refs.
- 2026-08-02: Wired diff/impact into initial submission, sync rewrite, durable
  rewrite, atomic apply, and apply audit details; added the revision-ledger UI
  display. Independent challenge found and closed three P1 classes: forged or
  unbound diff segments, unreadable sibling sections reported as `known`, and
  a sync-rewrite post-AI working-copy race. The contract now requires paired
  hashes and canonical full-sequence replay; impact reads fail closed; bound
  snapshots are revalidated before and after projection and repository
  identity checks apply even without the optional study-consistency service.
- 2026-08-02: Added deterministic regressions for forged diff text, missing
  paired hashes, unreadable sibling sections, and the sync rewrite race. Codex
  focused suite passed `150 passed, 106 deselected in 130.69s`; independent
  challenge reported `228 passed in 118.15s` and READY with no remaining P0-P4.
  Compileall and frontend Vite build passed; frozen r42 remained unchanged
  (`d354eb0b4f8b98225c831d76f752b346315949e0e78983f24c6392c91d255130`, mtime
  `2026-07-31 16:11:13 +0800`, size `6516`). No service, browser, real model,
  OCR/translation, download, upstream, or monitoring path was touched.
- 2026-08-02: `hermes_workflow_guard.py review-gate --require-verification`
  passed with no warnings or errors. This context/run/review/metrics quartet
  is the durable handoff; Goal remains active and the next safe action is a
  separately tracked Phase 0C increment.
