# Codex Review: mw_protocol_p0_phase0b_rebaseline_20260801

Date: 2026-08-01
Delegated-agent output: `runs/codex_mw_protocol_p0_phase0b_rebaseline_20260801.md`

## Verdict

`OFFLINE_SLICE_READY / PHASE_0B_RUNTIME_GATES_OPEN`

## Boundary Check

- Product edits are currently limited to the medical-writing contracts,
  protocol template/materializer, focused tests, and the medical-writing
  editor rendering in `App.jsx`/`styles.css`.
- No product implementation intentionally edited medical-monitoring source or
  logical data, and no r42 immutable state or runner-owned report was edited.
- Conference boundary compliance is not clean: a chair-run test imported the
  full application despite an explicit prohibition. Subsequent read-only
  forensics also refreshed monitoring SHM physical metadata. Relative to the
  old r42 snapshot, concurrent monitoring activity prevents a causal
  logical-delta attribution; this is recorded as a boundary deviation rather
  than incorrectly certified as zero delta.

## Codex Verification

- Official ICH M11 final guideline/template checked for structural-heading and
  explicit-not-applicable semantics.
- Deterministic phase probe: applicable unclassified nodes 0 for I/II/III;
  actionable blocker body pollution 0.
- Focused protocol/fact-intake/frontend-contract tests: 182 passed.
- Python compileall: passed.
- Frontend production build: passed; existing bundle-size warning remains.
- Browser/product-model/Word acceptance is deliberately still open.

## Delegated-Agent Output Review

Independent conference round 1 returned `REVISE`. Codex repaired its P1/P2
findings and the same Qwen chair session returned slice-level `READY` in round
2. Codex also closed the chair's remaining backend semantic-hash P2 and blank
draft intent-label P3 after that review. The runner is authoritative for two
same-session rounds; the chair report's narrative “four rounds” is treated as
advisory review-pass labeling, not runner evidence.

The later document-level aggregation delta was independently challenged and
returned no P0-P2 issue. Its product verdict remains offline READY, but the
chair's false no-main claim is rejected and is not acceptance evidence.

## Residual Risk

- Runtime/API/browser evidence is not yet available.
- The number of actionable blockers is intentionally large for sparse input;
  later orchestration must generate candidates in bulk and aggregate only
  genuinely high-impact decisions rather than asking the user chapter by
  chapter.
- Unknown/deferred optional modules remain omitted from clinical text; the
  new document-level readiness signal now aggregates them into one gate and
  one approval blocker.
- Full API/browser/product-model/Word evidence must run through a
  medical-writing-only isolated runtime or entrypoint. Importing the shared
  full application is not an acceptable next gate while monitoring runs in
  parallel.
- Process-level isolation is now proven: a full app import resolved to a new
  temp runtime, created all 12 monitoring SQLite/WAL/SHM files there, loaded
  326 routes, and left all 12 stable monitoring file fingerprints unchanged.
  This opens the isolated API/browser gate without accepting the shared full
  app as safe.

## Browser Gate Addendum

`RUNTIME_PARTIAL_READY / TRIAGE_RUN_PENDING`

- Real Computer Use reproduced and corrected two misleading UI states:
  failed research is no longer shown as complete, and neutral nested scaffolds
  no longer enable package adoption.
- A clean III-phase generalized-myasthenia-gravis project proved the registry
  resolver correction: 59 studies and 21 public Protocol documents were
  retained instead of the previous 0-result failure.
- The live run is now in AI triage and is not yet evidence for a completed
  Protocol flow, document preparation, translation, drafting, Word, or release
  gate.
- One mistyped pytest selector caused collection-time full-app import. No
  target test ran; it is recorded as a boundary deviation and was replaced by
  a pure three-test resolver suite. No shared-monitoring logical-zero claim is
  made.
- Event-driven follow-up at 10:50-10:53 CST observed the same run advance from
  chunk 3/6 to chunk 4/6, then remain unchanged through a later long wait.
  This is not a terminal failure and does not authorize re-dispatch or
  restart. Browser/Word/release acceptance therefore remains open.
- Subsequent same-run evidence closed the triage portion of this browser
  gate: 6/6 chunks completed on attempt 1, and the real basket UI exposed one
  AI-first confirmation for 59 classifications (21 retained, 38 excluded).
  That action successfully locked the scope and started the same pipeline's
  public-Protocol preparation; the first of 21 documents completed and the
  second started.
- oMLX runtime evidence is clean at this checkpoint: authoritative
  `GLM-OCR-bf16`, 8/8 OCR leases active, no queued or expired leases, and the
  source contract enforces 200-DPI evidence. The overall Protocol gate remains
  open because the 21-document preparation, translation/medical review,
  design completion, full draft, export, and Microsoft Word acceptance have
  not finished.

## OCR Cutover Review Addendum

`ROUTE_CORRECTION_ACCEPTED / LIVE_DOCUMENT_EVIDENCE_PENDING_TERMINAL`

- The user's latest route correction supersedes the earlier GLM-only test
  preference for not-yet-started files, while preserving GLM for every file
  already in progress.
- The official Paddle endpoint and encrypted credential were proven by a real
  200-DPI image request before cutover; a GLM fallback response would have
  failed this proof.
- Cutover occurred only after the exact GLM item reached `prepared`. No
  current-file model was changed and no prior extraction was replayed.
- The code-level document pin is now robust to later role changes and rejects
  unknown or unavailable pinned profiles. The focused 70-test suite and
  compileall passed.
- Runtime acceptance still requires the first post-cutover document's
  persisted extraction evidence to show Paddle as the actual model/provider,
  followed by completion of the remaining preparation and downstream gates.
- That evidence is now partially accepted: 28/31 pages are actual
  `paddle_official / PaddleOCR-VL-1.6`; three correctly attributed GLM
  fallbacks were caused by HTTP 429. Therefore the route is real but the
  first document is not single-model Paddle evidence.
- The automatic mixed-model QC correctly failed open-to-review rather than
  silently admitting the table pages. The remaining source-verification
  questions stay open.
- Provider-aware concurrency and bounded 429-only submit retry are implemented
  and deterministically verified for the next runtime. Ambiguous 5xx
  responses fail to the attributed fallback rather than risking a duplicate
  hosted job. These changes cannot affect the
  already-running process without an unsafe preparation interruption, so no
  restart was performed.
- The focused suite now has 72 passing tests, including an explicit
  single-attempt 503 assertion.

## Translation And Admission Review Addendum

`RUNTIME_ROUND1_MATERIAL_READY / DESIGN_SUGGESTION_RUNNING`

- The attempt-1 preparation and first-round analysis are complete.
- The failed-only retry contract was verified both from source and from the
  real SQLite delta: exactly two failed rows advanced to attempt 2; the
  18 nonfailed rows did not change attempt or identity.
- The new plan and upper-layer run are append-only. The prior failed Flash/Pro
  rows remain immutable and queryable.
- The final translation state contains four visible fidelity blocks. Batch
  medical review admitted only the two machine-passed candidates, so the
  fail-closed boundary is intact.
- The strengthened Paddle slice passes 106 focused tests and compileall.
  Participant READY findings do not replace the still-running chair or Codex
  final acceptance.
- The next user-facing risk is product behavior, not transport: the main form
  still exposes 13 unresolved design inputs. A single real `更新建议` request
  is now testing whether independent AI collapses these into a reviewable
  design package as required by the AI-first operating model.

## AI-first suggestion acceptance addendum

`NOT_READY / SOURCE-BOUND_PROTOCOL_EVIDENCE_NOT_IN_MODEL_CATALOG`

- The single real request terminated successfully at transport level but its
  package status is `partial`; 13 high-impact design fields remain delegated
  to the user. This is not an acceptable AI-first result.
- The failure is structural and reproducible from source: both generation and
  adoption validation rebuild an evidence catalog that omits the completed
  Protocol corpus-analysis run and its source bindings.
- The remediation must preserve competitor-evidence semantics: corpus
  findings may suggest options only for an explicit allowlist of design
  targets; they may never establish current-project facts. Stale analysis IDs,
  missing source spans, or hash/identity mismatch must fail closed.
- The declared execution is serial to avoid overlapping edits. Codex will not
  accept it until generation and adoption use the same catalog, deterministic
  tests prove allowed and rejected mappings, and the actual UI is rerun once
  in a fresh isolated runtime.

## Paddle chair challenge closure

`READY_WITH_P3_CLOSED`

- The chair's commit-window challenge was valid: repository idempotency
  previously prevented duplicate immutable rows but was reached only after
  OCR execution.
- The extraction service now checks a project/artifact-bound persisted
  idempotency result before reading or OCR-processing the artifact. Cross-
  artifact key reuse fails closed.
- The crash/restart regression proves one GLM model call, not merely one
  stored row. Current focused total: 107 passed.

## Corpus bridge correction review

`OFFLINE_CORE_READY / ADVERSARIAL_WORKER_AND_MANAGER_PENDING`

- The first implementation was correctly rejected despite green synthetic
  tests: it made every real single-source finding unbindable and therefore
  could not reduce blank-form burden.
- The same-session correction preserves the semantic distinction between
  “do not generalize” and “do not show”: single-source observations can now
  become source-specific pending choices, while conflicts still cannot become
  choices.
- Real runtime evidence passes analysis identity/hash and 8/8
  artifact/span/hash/current-state checks. Every reconstructed entry remains
  a competitor observation; none is a current-project fact.
- The old partial package is stale by construction. No old journey or package
  row was rewritten.
- Acceptance remains open until Worker 3 closes locator/exact-fact/adoption
  adversarial tests and Cursor manager reviews the complete implementation.

## Corpus bridge final runtime addendum

`RUNTIME_CORE_READY / INDEPENDENT_CONTRADICTION_REVIEW_PENDING`

- Offline implementation and adversarial acceptance were followed by four
  serial clean-clone runtime proofs. The final contract closes projection
  starvation, visible-gap omission, and model nondeterminism without
  promoting competitor evidence into project facts.
- Final r4 browser evidence shows only three explicit Protocol terms as
  AI-determined; ten other design decisions remain blank. The original quote,
  not-current-project warning, source-purpose limitations, and manual-only
  review state are visible.
- The final clone contains exactly one new generation event and one target
  revision. Nine non-authoring writing databases and all non-target journeys
  are logically identical to source; no adoption or upstream processing
  occurred.
- Two wording/UX questions remain for the declared independent challenge:
  repeated display of one quote for three claim bindings, and `当前0`
  independent-source/sponsor wording despite one visible source.
