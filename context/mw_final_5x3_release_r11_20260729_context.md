# Medical Writing Final 5x3 - release-r11-20260729

## Purpose

Run A1 lazy medical-writer acceptance from a completely clean runtime after
accepting the parent/child triage deadline reconciliation. This round is
immutable while its tester is active.

## Governing Receipts

- Global AGENTS SHA-256:
  `1d54ff677fb83d271492b32cecaa15b329f033d11e1759cb1fcb55c6bf0cab6a`
- Matrix:
  `scripts/qc/mw_final_5x3_matrix.json`
- Round:
  `runs/execution/mw_final_5x3_harness_20260728/rounds/release-r11-20260729`
- Input fingerprint:
  `9ff495f4a60163e4e5fa44da1081e265be0fd60e034638911739770a6f9e91ff`
- Accepted research-pipeline SHA-256:
  `5276cb545e5288a1efdfd71b5bb16f403ec8f910d0919c99122aa95b54d4f628`
- Accepted deadline regression SHA-256:
  `dd007523a1d4881274ccc8e2c55dbde2784a74f6c22a2b93b247d24a16d9bf2a`
- Isolated runtime identity:
  `44d3ba639af0972f091ab06530af446ff92567ca10badddfb71c114205b926fb`
- Frontend:
  `http://127.0.0.1:54664`
- Backend:
  `http://127.0.0.1:54663`

## Active Scope

- Slot/perspective: `A1/lazy_medical_writer`
- Tester: Codex subAgent `gpt-5.6-luna-high`
- Agent ID: `019fa97e-32f9-7a63-b644-39ab3f8eb6af`
- Scenario: COPD, Phase III, fixed-combination inhaled product, greenfield.
- The runtime, project, browser profile and ports must all be new.

## Acceptance Emphasis

1. Real visible desktop browser only; no hidden API mutation.
2. Product independent AI performs discovery, triage, preparation,
   extraction, translation/corpus preparation and writing.
3. Exactly one search and one parent start request reach the API.
4. The repaired parent recognizes the deadline-edge child and presents one
   bulk basket confirmation instead of retrying triage.
5. Basket confirmation advances into real preparation and translation work.
6. Continue through a complete protocol, DOCX, PDF and native Word inspection
   unless a material blocker is frozen first.
7. No override, skeleton prefill, fabricated AI output, or tester-authored
   protocol content can count as acceptance.
8. UX is assessed as a lazy but senior medical writer: AI defaults first,
   batch confirmation, no repetitive row-by-row approval, no log-heavy UI.

## Source Freeze

No product source, test source, matrix receipt or runtime database may be
modified while this tester is active. Context and evidence records may be
appended. If a material blocker is found, freeze evidence, stop isolated
services, then repair and create a new immutable round.

## Next Safe Action

The tester has completed and the round is permanently classified as FAIL /
BLOCKED. Preserve the frozen evidence, diagnose the candidate-projection
failure without mutating this runtime, repair only after the root cause is
proved, and retest from a new isolated round.

## Live Observations

- Project: `proj_user_d9cd77c5ef5e`
- Snapshot: `wref_search_9e59d59c6cf7e5a6924d`
- Parent pipeline: `mwpipe_8f96ef8efa2bb9182a39`
- Parent durable job: `mwjob_71a85c0f5b9a4489892e537b`
- Triage run: `ct_run_b9528143bcecc173f381`
- Triage durable job: `mwjob_7b5f19692f95bdd147a860ae`
- At 2026-07-29 00:33 Beijing, the durable child had completed 7/19 chunks
  (37%, 594 deterministic records; AI batch 3/15) while the parent still
  exposed the coarse fixed `triaging` value 22%. This is direct runtime
  evidence for the already-recorded weighted-progress gap; it is not being
  repaired during the source-frozen round.
- At 2026-07-29 01:06 Beijing, the same triage run reached 19/19,
  `review_ready`; the parent reached `awaiting_triage_confirm` without a new
  child or a false timeout. The r10 deadline-edge repair therefore passed its
  real-runtime gate.
- The tester issued exactly one visible bulk-confirm request for
  `ct_run_b9528143bcecc173f381`. The pipeline advanced to `preparing` with
  preparation batch `wref_prep_421949bdd4c543d72a61470f`, 53 retained
  candidates, 99 public documents and a concrete live item label
  (`NCT02497001 / Prot_001.pdf`).

## Terminal Result

- Tester result: `BLOCKED`; PASS is forbidden for this immutable round.
- First material blocker:
  after the confirmed basket was reopened in the real browser, the candidate
  tab displayed `0项 / 尚未检索公开竞品研究`, although the durable triage run
  remained confirmed with 53 retained and 612 excluded studies.
- The preparation child processed 99/99 documents and stopped at
  `awaiting_document_validation`; 59 documents did not pass admission and
  3 documents failed. This is a separate downstream condition and must not be
  silently treated as the cause of the empty candidate projection.
- Downstream validation, translation, corpus admission, complete protocol,
  DOCX, PDF and native Word gates were not reached.
- Evidence:
  `runs/execution/mw_final_5x3_harness_20260728/rounds/release-r11-20260729/slots/A1/lazy_medical_writer/`.
- Isolated services were stopped and ports released on 2026-07-29; stopped
  PIDs were `86381` and `86364`.
- No product source, test source, matrix receipt, or frozen runtime database
  was modified by the tester.
