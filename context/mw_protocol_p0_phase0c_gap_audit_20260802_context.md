# Task Context: mw_protocol_p0_phase0c_gap_audit_20260802

Created: 2026-08-01 23:44:47
Objective: 继续 Protocol P0：审计并推进局部 AI 精改、稳定语义选区、局部 diff/影响与可信 DOCX 预览的最小可验证闭环；不触碰冻结 r42/v36、上游研究/OCR/翻译或医学监查并发线
Task type: `clinical_document_router`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `runs/MW_R42_NO_LOSS_PAUSE_20260731_1609.md` (immutable r42 boundary and
  frozen-stage inventory).
- `plans/mw_commercial_writing_gap_and_roadmap_20260731.md` (approved
  Protocol-first roadmap; Phase 0C contracts and exit gates).
- `context/mw_commercial_writing_gap_20260731_context.md` and
  `reviews/mw_commercial_writing_gap_20260731_independent_challenge.md`
  (approved product model and independent challenge deltas).
- Current Protocol authoring source, tests, generated frontend build and
  isolated runtime evidence under this workbench. The current filesystem is
  authoritative; prior records are evidence, not permission to rerun frozen
  work.
- Existing Phase 0B post-corrective acceptance records:
  `context/mw_protocol_p0_phase0b_postcorrective_acceptance_20260801_context.md`,
  `runs/codex_mw_protocol_p0_phase0b_postcorrective_acceptance_20260801.md`,
  `reviews/codex_mw_protocol_p0_phase0b_postcorrective_acceptance_20260801_review.md`,
  and `metrics/mw_protocol_p0_phase0b_postcorrective_acceptance_20260801_metrics.md`.
- No external generation, OCR, translation, download, or paid platform action
  is an authority or a permitted input for this bounded audit.

## Scope

- In scope:
  - Read-only audit of the current local AI edit, semantic-range/identity,
    diff/impact and DOCX preview/export contracts and their focused tests.
  - Select one smallest missing or weak contract that can be isolated from
    r42/v36 and the upstream evidence pipeline.
  - If justified, implement only that local product/test change, with focused
    deterministic verification and an isolated runtime/browser/document
    recheck.
  - Preserve an auditable run, review and metrics record for the exact change.
- Out of scope:
  - Any r42 retry, batch/item transition, preparation, download, OCR,
    translation, attempt 2/3, ready/excluded item, existing idempotency key,
    or mutation of immutable fidelity-blocked rows.
  - Synopsis, CSR, final three-route/two-role release testing, production
    promotion, or broad architecture refactoring.
  - Starting services or invoking product AI before a bounded implementation
    and test contract is established.
  - The concurrent medical-monitoring lane and any unrelated user changes.

## Success Criteria

- Phase 0C minimum identity contract is explicit before local AI editing:
  product/block/range/revision/selected_hash/claim/source/snapshot must be
  stable or fail closed.
- Local intent operations (rewrite/expand/reduce/polish/custom) must target
  an unambiguous, current semantic range and preserve protected facts,
  numeric/unit/citation tokens and confirmed study facts.
- Stale, ambiguous, or duplicate ranges must not write content or create an
  accepted revision; a rejected operation must be observable and auditable.
- Diff/accept/reject/undo and downstream impact must refer to one immutable
  snapshot; no silent whole-chapter rewrite.
- Fast preview and DOCX export must expose their snapshot/revision identity;
  a quick preview must not be labeled as Word-verified.
- Any source edit must be minimal, reversible, and covered by focused tests;
  existing r42/clone invariants remain byte/logically unchanged.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- Never modify `runs/MW_R42_NO_LOSS_PAUSE_20260731_1609.md` or the original r42
  runtime/database. Only task-scoped context/run/review/metrics and explicitly
  related Protocol authoring source/tests may change.
- No credentials, authenticated traces, or unredacted clinical content may be
  persisted in task records.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-01 23:44:47: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-02: Re-anchored global/workspace/workbench/frontend instruction files,
  r42 pause checkpoint, approved commercial gap roadmap, context and
  independent challenge. Phase 0B post-corrective slice remains bounded READY;
  Goal remains active.
- 2026-08-02: Next loop is read-only Phase 0C surface audit. Expected signal is
  one isolated contract gap with a deterministic test path; if no such gap is
  proven, stop without product mutation and record the evidence.
- 2026-08-02: Audit found that `normalize_revision_selection` selected the
  first substring/block when the same selection was repeated. The durable
  submit path also skipped this normalization for lightweight/greenfield
  documents, so an ambiguous request could create a durable job before later
  failure. This was selected as the sole bounded gap.
- 2026-08-02: Minimal corrective patch applied only to
  `services/api/app/medical_writing_repository.py` and
  `services/api/app/medical_writing.py`; focused regressions added to
  `tests/test_medical_writing_revision_application.py` and
  `tests/test_medical_writing_revision_durable.py`. The repository now rejects
  repeated matches within an anchored block and matches across multiple
  unanchored blocks; durable submission resolves the exact selection before
  `create_or_reuse`, so no job/idempotency row can be created for an ambiguous
  range. Existing project-isolation fixture was updated to use real source
  anchors under the stricter contract.
- 2026-08-02: Deterministic verification passed: both revision suites
  `59 passed in 50.35s`; the regression includes overlapping same-block
  matches (for example `aaa` in `aaaa`), non-overlapping same-block matches,
  and cross-block matches. Frontend medical-writing contract subset `16
  passed`.
  Frozen r42 checkpoint remains unchanged (mtime `2026-07-31 16:11:13 +0800`,
  SHA-256 `d354eb0b4f8b98225c831d76f752b346315949e0e78983f24c6392c91d255130`).
  No service, browser, product AI, OCR, translation, download, or upstream
  runtime was started in this loop.
- 2026-08-02: Independent read-only challenge requested from the existing
  native Codex reviewer; no file edits were permitted. The final handoff and
  Codex boundary review are now complete below.
- 2026-08-02: Independent challenge found and closed one additional case:
  unanchored selection with exactly one matching block but repeated text
  inside that block. The same overlapping occurrence counter now runs in both
  anchored and unanchored branches; durable preflight has explicit no-anchor
  regression and still creates zero jobs. A fresh full-suite run after this
  correction returned `59 passed in 50.35s`; independent reviewer is performing
  one final same-session verification against the new source hashes.
- 2026-08-02: Independent final handoff returned `READY` for this bounded
  paragraph-selection/durable-preflight slice. It independently reran the two
  decisive ambiguity/no-job tests (`2 passed in 2.08s`) with unchanged final
  hashes: `medical_writing.py` `3b95e2004f6cabef24ed5f4f2082b8bce23f83f949bba6b7d6d3f09df904792c`,
  `medical_writing_repository.py`
  `4642099b3ff9f1f026d17a77fdcfcace75b482fc6d3fcb3ecce1a3b3508447c7`,
  application test `a32e82d6c5011ec5381f33c7fe24eed9f3ba5c34969a4d8fb7cc731f642b0c57`,
  durable test `64c989d9ab9bea1f8a3656c4d491c0fbaad8050053f23cdfe6f8482388acd254`.
  It confirmed blank greenfield and table-cell branches remain isolated and
  found no frozen-state write entry. Non-blocking evidence limits: no new
  direct table-cell/blank-greenfield durable-preflight test was needed for this
  bounded paragraph patch; branch isolation and existing tests remain the
  evidence.
- 2026-08-02: Hermes workflow guard review gate passed for the final
  review/metrics pair with `ok=true`, `warnings=[]`, `errors=[]`.
- 2026-08-02: Final read-only process check found no listener on task-scoped
  ports `18905/18906`. Pre-existing unrelated listeners (`9100`, `15174`,
  `18911`) and the shared `omlx-server` were not started, stopped, or modified
  by this task.
