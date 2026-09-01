# Codex Conference Review: eligibility_evidence_review_vertical_20260711

Date: 2026-07-11

## Verdict

Final conference verdict: **pass with a bounded implementation gate**. All participant outputs are substantive. The Reasonix DeepSeek Pro main venue accepted Codex's corrections to the Hermes chair package. Production implementation may begin with rule/source identity and the review persistence foundation; OCR/VLM and AI-result generation remain gated by their task-specific quality probes.

## Boundary Compliance

- Qwen, Mimo, DeepSeek Flash, and the Hermes chair wrote only their assigned files under `runs/`.
- No conference participant was authorized to read raw patient files, production SQLite, runtime secrets, or legacy eligibility conclusions.
- Provider/model markers were observed in stdout for `qwen3.7-plus`, `mimo-v2.5`, `minimax-m3`, and Reasonix `deepseek-v4-flash`; no silent model substitution was accepted.
- Codex retains authority for source-file probes, production edits, browser/visual checks, and clinical conclusions.

## Participant Outputs Reviewed

- `participant_qwen_plus.md`: incorporated. Strong on bounded semantic batches and human confirmation, but its proposed Hermes-directory storage is rejected.
- `participant_mimo.md`: incorporated. Strong on explicit state/CAS design, but SQLite BLOB evidence storage, sequential batch blocking, and silent local-model fallback are rejected.
- `participant_ds_flash.md`: incorporated. Strong on version identity, hybrid evidence storage, adversarial tests, and API envelopes. Its whole-rule-set numbering block and subject-level extraction gate are too strict.

## Hermes Sub-Venue Review

The chair compared all participants and added useful privacy, audit, desktop, and six-subject perspectives. Codex does not accept these chair conclusions without revision:

1. Missing original Word display numbering does not block the entire project. `criterion_uid` binds to canonical project, source revision, source locator, and normalized criterion text. A generated `IN-xx`/`EX-xx` is allowed only when explicitly labelled as a system review ID; ambiguous criterion extraction itself still blocks writes.
2. OCR/output storage must use the workbench-controlled artifact root, never `~/.hermes` or another agent-specific directory.
3. Evidence processing state and medical decision state remain orthogonal. Unprocessed sources defer a criterion; they do not create `insufficient_evidence`.
4. Independent AI batches may succeed or fail independently. A failed batch blocks only its own unresolved criteria and the subject aggregate, not later independent batches.
5. No silent AI-provider fallback is permitted. Route failure becomes an auditable task failure and visible disabled/error state.
6. This slice does not produce a formal eligible/not-eligible conclusion or randomization release.

## Main-Venue DeepSeek Pro Review

Reasonix `deepseek-pro` completed and independently accepted these boundaries:

- Per-criterion numbering tolerance with clearly labelled system review IDs; no whole-project block for missing source display numbers.
- Workbench-controlled hybrid evidence artifacts plus SQLite metadata; no Hermes directory and no SQLite BLOB evidence body.
- Independent AI batches with per-rule fallback; one failed batch does not suppress unrelated criteria.
- Separate IN/EX decision enums, no generic pass/fail and no formal eligibility release in this slice.
- `BEGIN IMMEDIATE` CAS with rule, subject-source and state revisions plus criterion-scoped idempotency.
- Epoch/request-token validation before desktop writes.

Codex rejects one new internal contradiction in the main review: the EX batch must not consume an IN-decision summary if IN and EX are defined as independently executable. Both consume the same versioned evidence fact ledger; cross-batch AI conclusions are not inputs.

## Codex Independent Verification

Already verified:

- Real protocols parse independently to D001 6 IN/30 EX and MY009 10 IN/24 EX with original DOCX paragraph locators.
- Current IDs are positional system labels; public rule/source versions do not yet bind all source content changes.
- Current UI is a read-only pool/rule browser and has a subject-switch stale-detail race before criterion-level writes are added.
- One real D001 image completed local PaddleOCR-VL-1.6 inference in 11.14 seconds with 6,497 characters; no patient text was copied into conference files.
- Six fixed subjects contain 269 PDF pages, 267 of them scan/low-text pages, plus 22 images. OCR therefore must be asynchronous, resumable, page-cached, and independently retryable.
- Both real DOCX rule sections use continuous level-0 decimal numbering starting at 1 with no `startOverride`: D001 numIds 41/42 and MY009 numIds 67/70. All 70 top-level criteria have unique paragraph locators and unambiguous text in the current source versions.
- Three text-bearing real images completed on both local OCR models. GLM produced 745-942 characters; PaddleOCR-VL produced 776-943 characters. Both models found all four predefined visible anchors on the independently inspected D001 record image.
- Three D001 full-body/lesion photographs correctly produced no substantive Paddle OCR text; GLM returned the same 16-character no-text response. These files require visual-evidence/VLM classification, not OCR evidence conclusions.

Still required before OCR/AI generation is enabled:

- Extend portable numbering fixtures for restart/manual-override cases; the two current real protocols passed but do not cover every future DOCX pattern.
- Add OCR/VLM media classification, asynchronous page jobs, cancellation, cache keys, memory telemetry and sampled visual-QC status. Local HTTP invocation and text-image extraction are verified; clinical photographs must be routed separately.
- Verify a task-specific external-AI JSON contract; no Codex inference may populate runtime results.
- Run SQLite v6 backup/migration/integrity/CAS tests on an isolated copy before touching the active database.
- Fix and browser-test cross-project and cross-subject stale-response races before enabling writes.

## Final Decision

**Pass for bounded implementation.** The accepted architecture is: content-bound source/rule identities, workbench-controlled evidence artifacts plus SQLite metadata/audit state, asynchronous source-page fact ledger, media classification to OCR or VLM, independent 5-8-criterion AI batches with partial success and per-rule fallback, separate IN/EX decision enums, medical confirmation with CAS/idempotency, and a desktop three-column review surface.

Implementation starts with identity/contracts and additive SQLite v6 on isolated copies. No AI draft or medical conclusion may be generated until evidence locators and task-specific external-AI output validation pass. No cross-batch AI summary, no silent model fallback, no legacy verdict input and no formal eligibility release are allowed.
