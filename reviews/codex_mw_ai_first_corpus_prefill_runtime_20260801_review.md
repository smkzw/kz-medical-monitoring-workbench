# Codex Review: mw_ai_first_corpus_prefill_runtime_20260801

Date: 2026-08-01
Runtime evidence: `runs/pi_mw_ai_first_corpus_prefill_runtime_20260801.md`

## Interim Verdict

`CORE_READY / INDEPENDENT_CONTRADICTION_REVIEW_PENDING`

The final isolated runtime meets the source-binding, fail-closed, one-request,
append-only, and user-visible-evidence requirements. Final acceptance is held
only for the declared independent review, not for another runtime generation.

## Boundary Check

- Existing API/frontend 18911/15174 and source runtime were not restarted or
  mutated.
- All runtime writes occurred in serial temporary clones; only the final r4
  clone is retained for review.
- No preparation, triage, OCR, translation, admission, blocked-item, Synopsis,
  CSR, or medical-monitoring action was run.
- No candidate was adopted. The pre-existing adoption event count is unchanged
  source versus clone.
- Product-source edits are limited to the authoring prefill evidence binding,
  AI orchestration, and focused tests from this task. Unrelated monitoring
  files were not edited.

## Codex Verification

- 480 focused tests passed; 17 warnings are pre-existing deprecations.
- Python compilation passed.
- One real Computer Use click produced one new rev7 generation event.
- Real Chrome inspection proved:
  - explicit three-term candidate preview;
  - original Protocol text visible;
  - not-current-project and single-source limitations visible;
  - exactly three AI-determined fields;
  - ten remaining fields blank;
  - pending review and disabled adoption.
- SQLite logical comparison proves all non-authoring writing stores are
  identical and the authoring clone differs only by the target rev7 journey
  state plus one generation event.

## Open Challenge Items

- The same source quote renders three times because each claim has a separate
  binding. This is auditable but visually redundant.
- Evidence-gap text says independent source/sponsor count is `0` although the
  candidate visibly has one source. This may mean zero qualifying independent
  corroborators, but the wording is ambiguous.
- The independent reviewer must decide whether either issue is P0-P4 and
  whether a bounded correction is required before runtime acceptance.

## Residual Risk

- This accepts only the corpus-to-review-candidate bridge. It does not accept
  complete Protocol drafting, export, Microsoft Word fidelity, Synopsis, CSR,
  or the frozen final multi-model release loop.
- The r4 services remain active only until independent review finishes; they
  will then be stopped without deleting the auditable clone.

## Post-Conference Corrective Review Addendum

The prior open challenge items and additional P2-P4 findings were corrected.
Codex's current bounded verdict is:

`POST_CORRECTIVE_RUNTIME_READY / NEW_INDEPENDENT_CHALLENGE_PENDING`

- Evidence references are deduplicated while atomic bindings remain.
- Qualifying independent support and bound-source counts are separately
  worded.
- Pending/manual candidates cannot use the single-card adoption path.
- Generation has a durable one-attempt reservation and fail-closed restart
  semantics.
- Empty recommendation is persisted when no safe candidate exists.
- r5's context-free `是` preview was corrected to `开放标签延展`.
- r6 real Chrome and SQLite evidence passed with one generation and zero
  adoption; 601 focused tests pass.

Final acceptance is now held only for a new independent challenge against the
post-corrective source and r6 evidence.

## Second Challenge Corrective Acceptance Addendum

The new independent challenge completed and its bounded P2-P4 findings were
corrected through the tracked execution
`mw_ai_first_prefill_postchallenge2_corrective_20260801`.

Current bounded verdict:

`POSTCHALLENGE2_CORRECTIVE_ACCEPTED / USER-REQUESTED NO-LOSS PAUSE`

- Three serial DeepSeek V4 Flash workers and Cursor manager completed without
  fallback.
- Manager authoring-focused tests: 727 passed.
- Codex expanded focused tests: 748 passed, 17 baseline warnings; frontend
  Node QC passed.
- The r7 online-backup child of r6 passed 21 SQLite quick checks.
- Computer Use on the real r7 surface proved the empty-slot, disabled unsafe
  actions, 13-path confirm-or-skip gate, and absent dead single-card adoption.
- Acceptance traffic was GET-only: no model call, generation, adoption, or
  product write.
- r7 and r6 match logically for all 21 SQLite stores.
- All r4-r7 API/Vite listeners were stopped and their clones preserved.

This accepts the bounded AI-first prefill corrective stage, not the complete
Protocol, DOCX/export, Synopsis, CSR, or final release matrix. The exact resume
boundary is
`runs/MW_AI_FIRST_PREFILL_POSTCHALLENGE2_NO_LOSS_PAUSE_20260801_2124.md`.
