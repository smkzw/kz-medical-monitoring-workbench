# Medical Writing Final 5x3 - release-r10-20260728

## Purpose

Re-run A1 lazy medical-writer acceptance from a completely clean runtime after
the accepted parent research-pipeline atomic-start repair. This round is
immutable while its tester is active.

## Governing Receipts

- Global AGENTS SHA-256:
  `1d54ff677fb83d271492b32cecaa15b329f033d11e1759cb1fcb55c6bf0cab6a`
- Matrix:
  `scripts/qc/mw_final_5x3_matrix.json`
- Round:
  `runs/execution/mw_final_5x3_harness_20260728/rounds/release-r10-20260728`
- Input fingerprint:
  `b66660097d1a3fb1cc59c3217798a7af20d2c1d43ee43de611006f5aa87ed138`
- Refreshed authoring-journey SHA-256:
  `95156b6798d940fe1cd7b83444c7c3c4a76ac88ddba9b7e45276331fe84c5bea`
- Isolated runtime identity:
  `ac290fa59e35bdbd4a44ec70d5d71a1479d327b921ac59ae54ffdb3c6198f498`
- Frontend:
  `http://127.0.0.1:51567`
- Backend:
  `http://127.0.0.1:51566`

## Active Tester

- Slot/perspective: `A1/lazy_medical_writer`
- Tester: Codex subAgent `gpt-5.6-luna-high`
- Agent ID: `019fa927-1420-7ba3-89e7-500c75781a89`
- Scenario: COPD, Phase III, fixed-combination inhaled product, greenfield.
- Started: 2026-07-28 22:35 Beijing.

## Acceptance Emphasis

1. Real visible desktop browser only.
2. Product independent AI performs discovery, triage, download, extraction,
   translation/corpus preparation and writing; the tester does not substitute
   its own content.
3. After successful competitor search, exactly one parent
   `research-pipeline/start` request reaches the API.
4. The parent pipeline exists before the one permitted basket confirmation.
5. The retained basket advances into real preparation and translation work;
   translation latest/preview no longer return 404 for the bound snapshot.
6. Continue through full protocol, DOCX, PDF and native Word inspection unless
   a material product blocker is frozen first.
7. No override, skeleton prefill, hidden API mutation or source edit can be
   counted as acceptance.

## Source Freeze

No product source, test source, matrix receipt or runtime database may be
modified while this tester is active. Non-product context and evidence records
may be appended. If a blocker is found, stop the isolated services before any
repair and create a new immutable round after the repair is accepted.

## Next Safe Action

Wait sparsely for the tester terminal result. On PASS, close the tester and
continue A1 engineer in another clean runtime. On BLOCKED/FAIL, freeze evidence,
stop runtime, repair only the reproduced cause, refresh source receipts and
create release-r11.

## Terminal Result

- Status: `BLOCKED / FAIL`, never PASS.
- Runtime stopped and ports released.
- Project: `proj_user_04faaf78e0e0`.
- Snapshot: `wref_search_4825bab95e5d06f40b22`.
- Parent pipeline: `mwpipe_a404afb7561191463d88`.
- Child triage:
  `ct_run_a9f21b2407036d970744`,
  durable job `mwjob_d16bcddd5c969377bfa2a366`.
- The atomic-start repair passed real runtime verification:
  competitor search HTTP 200 exactly once, parent start HTTP 200 exactly once,
  and a non-empty parent pipeline existed before basket confirmation.
- New blocker:
  the child reached `completed/review_ready` at
  `2026-07-28T15:20:54.919462Z`, but the parent reached its 900-second polling
  boundary and persisted `分诊超时` at
  `2026-07-28T15:20:56.043539Z`.
- The parent had already retried three attempts. Its final 2.5-second poll
  interval missed a child completion about 1.1 seconds before the deadline.
- No basket confirmation, preparation batch, translation batch, protocol,
  DOCX, PDF or native Word acceptance was performed.
- Evidence:
  `runs/execution/mw_final_5x3_harness_20260728/rounds/release-r10-20260728/slots/A1/lazy_medical_writer/`.

## Repair Boundary

Before release-r11, add one final authoritative durable-child and bound
triage-run reconciliation at the timeout boundary. Promote the same
review-ready run to `awaiting_triage_confirm`; only a genuinely incomplete
child may remain a timeout. Do not extend the timeout to mask the race, create a
new triage run, repeat AI work or alter downstream gates.
