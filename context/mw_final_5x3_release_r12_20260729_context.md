# Medical Writing Final 5x3 - release-r12-20260729

## Purpose

Run a completely fresh A1 lazy-medical-writer acceptance after accepting the
r11 repair bundle:

- candidate drawer closed-to-open refresh;
- official ClinicalTrials.gov Protocol/SAP document identity authority;
- OCR native/OCR evidence reconciliation repair;
- four independently configurable AI roles with a real OCR visual probe;
- persisted, weighted, truthful research-pipeline progress.

This round is immutable while its tester is active.

## Governing Receipts

- Global AGENTS SHA-256:
  `1d54ff677fb83d271492b32cecaa15b329f033d11e1759cb1fcb55c6bf0cab6a`
- Matrix:
  `scripts/qc/mw_final_5x3_matrix.json`
- Round:
  `runs/execution/mw_final_5x3_harness_20260728/rounds/release-r12-20260729`
- Input fingerprint:
  `3a6fbb6bb82f02a6a911a9da61f37a4895fb56e24251fd7140507dd513a0ea2a`
- Research pipeline:
  `06dc4e0bcc186bd78f73ab3bf98abc94ca6b2460e2c610e5cba6e31d08c44090`
- AI role settings:
  `e6791e33471de4f3783e696ab75439f5f5d1493a96ba766ef97592f624e551d7`
- API composition root:
  `16c092e99a8cbb73f198ee24932a079121bc095455e82fa2fb7d0b94671d3464`
- Main frontend:
  `302981dff16196189668c7fc91e8d5c71165851389a78836e427bccb1488af2e`
- Authoring setup:
  `24629a2c8d1172947edf8c8d2062a6ea66e35ed956a783c4177872d75ad1fa8a`
- Candidate drawer:
  `2c7a9e2a869389f573ab694fb6b643732e705f7475902891f47bf3750a9b010f`
- Writing reference panel:
  `51b68772193c824d7cbb00a2f6bd350c4f9bfb1fc79f5b0c28489c4672641303`

## Active Scope

- Slot/perspective: `A1/lazy_medical_writer`
- Tester: Codex subAgent `gpt-5.6-luna-high`
- Scenario: COPD, Phase III, fixed-combination inhaled product, greenfield.
- Runtime, project, ports, and visible browser state must be new.

## Acceptance Emphasis

1. Use the real visible desktop UI; do not mutate product state through hidden
   API calls.
2. The product independent AI performs discovery, triage, document
   preparation, OCR, translation, corpus construction, and writing. The tester
   evaluates it and does not substitute for it.
3. Candidate drawer reopening must load the persisted confirmed basket and
   must never render a loading state as `0项`.
4. Registry-labelled Protocol/SAP documents must be admitted by official
   registry metadata unless content proves they are publications or the wrong
   trial/document.
5. Image-only pages must retain OCR evidence without claiming native/OCR
   reconciliation when no native span exists.
6. Parent and child progress must advance from real counters, display the
   current concrete substep, survive reload, and reset correctly after a retry.
7. Four AI roles must use their selected provider/Base URL/model/credential;
   oMLX owns only OCR/translation leases.
8. Continue through complete protocol, DOCX, PDF, and native Word inspection
   unless a material blocker is frozen first.
9. No override, skeleton prefill, fabricated AI output, or tester-authored
   protocol content can count as acceptance.
10. UX is assessed as a lazy but senior medical writer: AI defaults first,
    batch confirmation, no repetitive row-by-row approval, concise progress,
    and no log-heavy interface.

## Source Freeze

No product source, test source, matrix receipt, or isolated runtime database may
be modified while the tester is active. Context and evidence records may be
appended. If a material blocker is found, freeze evidence, stop services,
repair only after root cause is proved, and create a new round.

## Loop Log

- 2026-07-29 03:42 Beijing: source receipts validated; harness regression
  `69 passed`.
- 2026-07-29 03:43 Beijing: r12 preparation round created with a fresh input
  fingerprint. No product project or product AI call exists yet.
- 2026-07-29 03:44 Beijing: isolated A1 startup reached healthy API, zero
  projects, four runnable role bindings, and frontend startup, then failed
  `/api/runtime-readiness` with HTTP 503. The orchestrator stopped both
  processes; no tester, project, or product-AI pass was created.
- Root cause: the new comprehensive-AI role pointed to
  `independent_ai__alibaba_qwen38`, while the legacy
  `active_profile_id` remained `alibaba_qwen38`. Runtime readiness still
  resolved the legacy profile and failed closed on the mismatch even though
  role status correctly reported the comprehensive role runnable.
- r12 is permanently retained as a pre-tester startup failure. Product source
  was repaired only after both processes were proven stopped. It must not be
  reused for acceptance.

## Next Safe Action

Validate the comprehensive-role source-of-truth repair, update matrix receipts,
prepare a new r13 round, and only then start a fresh A1 runtime and visible
browser tester.
